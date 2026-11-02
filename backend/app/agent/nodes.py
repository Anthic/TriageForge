"""LangGraph nodes implementing autonomous decision making, tool execution, and structured finalization."""

import json
import time
from datetime import UTC, datetime
from functools import lru_cache
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.rate_limiters import InMemoryRateLimiter
from langchain_groq import ChatGroq

from app.agent.output_policy import apply_business_rules
from app.agent.prompts import SYSTEM_PROMPT
from app.agent.state import AgentState
from app.core.config import settings
from app.core.logging import logger
from app.schemas.triage import TraceStepType, TriageResult
from app.tools.mock_tools import ALL_TOOLS

# Shared in-memory rate limiter across all concurrent ticket invocations
rate_limiter = InMemoryRateLimiter(
    requests_per_second=settings.llm_requests_per_minute / 60.0,
    check_every_n_seconds=0.1,
    max_bucket_size=settings.llm_requests_per_minute,
)


def _build_model(model_name: str) -> ChatGroq:
    """Builds a configured Groq chat model with shared rate limiting."""
    if not settings.groq_api_key:
        raise RuntimeError("GROQ_API_KEY is not configured")
    return ChatGroq(
        model=model_name,
        api_key=settings.groq_api_key,
        temperature=0.0,
        timeout=float(settings.llm_timeout_seconds),
        max_retries=settings.llm_max_retries,
        rate_limiter=rate_limiter,
    )


@lru_cache(maxsize=1)
def get_agent_llm():
    """Returns cached tool-bound LLM with optional fallback for agent_node."""
    primary = _build_model(settings.groq_model).bind_tools(ALL_TOOLS)
    if settings.llm_fallback_model:
        fallback = _build_model(settings.llm_fallback_model).bind_tools(ALL_TOOLS)
        return primary.with_fallbacks([fallback])
    return primary


@lru_cache(maxsize=1)
def get_finalize_llm():
    """Returns cached structured output LLM with optional fallback for finalize_node."""
    primary = _build_model(settings.groq_model).with_structured_output(TriageResult)
    if settings.llm_fallback_model:
        fallback = _build_model(settings.llm_fallback_model).with_structured_output(TriageResult)
        return primary.with_fallbacks([fallback])
    return primary


async def agent_node(state: AgentState) -> dict[str, Any]:
    """Evaluates ticket and decides whether to call a tool or proceed to finalize."""
    trace = list(state.get("trace", []))
    existing_messages = list(state.get("messages", []))

    if state.get("tool_calls_made", 0) >= settings.max_tool_calls:
        response = AIMessage(content="The tool call limit has been reached. Finalize using the available information.")
        return {"messages": [response], "trace": trace}

    llm = get_agent_llm()

    # Initialize conversation with system prompt and customer ticket if first call
    initial_msgs = []
    if not existing_messages:
        ticket = state["ticket"]
        ticket_context = (
            f"TICKET METADATA:\n"
            f"- Ticket ID: {ticket.get('id')}\n"
            f"- User ID: {ticket.get('user_id')}\n"
            f"- Order ID: {ticket.get('order_id') or 'None'}\n\n"
            f"CUSTOMER MESSAGE:\n\"{ticket.get('text')}\""
        )
        initial_msgs = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=ticket_context),
        ]
        messages = initial_msgs
    else:
        messages = existing_messages

    start_time = time.perf_counter()
    response: AIMessage = await llm.ainvoke(messages)
    duration_ms = int((time.perf_counter() - start_time) * 1000)

    logger.info("agent_node completed in %dms (tool_calls=%s)", duration_ms, bool(getattr(response, "tool_calls", None)))

    # Record reasoning if model produced text before/alongside tool calls
    if response.content and str(response.content).strip():
        step_num = len(trace) + 1
        trace.append({
            "step": step_num,
            "node": "agent_node",
            "type": TraceStepType.REASONING.value,
            "reasoning": str(response.content).strip(),
            "duration_ms": duration_ms,
            "timestamp": datetime.now(UTC).isoformat(),
        })

    return {
        "messages": initial_msgs + [response],
        "trace": trace,
    }


async def tool_node(state: AgentState) -> dict[str, Any]:
    """Executes tool calls with strict prompt-injection argument validation."""
    messages = state["messages"]
    last_message = messages[-1]
    trace = list(state.get("trace", []))
    ticket = state["ticket"]
    tool_map = {t.name: t for t in ALL_TOOLS}
    tool_calls_made = state.get("tool_calls_made", 0)

    tool_outputs: list[ToolMessage] = []

    for call in getattr(last_message, "tool_calls", []):
        tool_name = call["name"]
        tool_args = call.get("args", {})
        call_id = call.get("id", f"call_{len(trace)+1}")

        if tool_calls_made >= settings.max_tool_calls:
            error_output = {"error": "MAX_TOOL_CALLS_EXCEEDED"}
            tool_outputs.append(ToolMessage(content=json.dumps(error_output), tool_call_id=call_id))
            trace.append({
                "step": len(trace) + 1,
                "node": "tool_node",
                "type": TraceStepType.ERROR.value,
                "tool": tool_name,
                "parameters": tool_args,
                "raw_output": error_output,
                "duration_ms": 0,
                "timestamp": datetime.now(UTC).isoformat(),
            })
            continue

        tool_calls_made += 1
        trace.append({
            "step": len(trace) + 1,
            "node": "tool_node",
            "type": TraceStepType.TOOL_CALL.value,
            "tool": tool_name,
            "parameters": tool_args,
            "timestamp": datetime.now(UTC).isoformat(),
        })

        # Security Guard: Validate IDs against ticket metadata (Prompt-Injection Protection)
        security_violation = False
        if tool_name == "get_order_status":
            expected_order = ticket.get("order_id")
            passed_order = tool_args.get("order_id")
            if not expected_order or passed_order != expected_order:
                security_violation = True
        elif tool_name == "get_user_tier":
            expected_user = ticket.get("user_id")
            passed_user = tool_args.get("user_id")
            if not expected_user or passed_user != expected_user:
                security_violation = True

        if security_violation:
            logger.warning("Prompt-injection blocked for tool %s", tool_name)
            error_output = {"error": "TOOL_ARGUMENT_REJECTED"}
            tool_outputs.append(ToolMessage(content=json.dumps(error_output), tool_call_id=call_id))
            trace.append({
                "step": len(trace) + 1,
                "node": "tool_node",
                "type": TraceStepType.ERROR.value,
                "tool": tool_name,
                "parameters": tool_args,
                "raw_output": error_output,
                "duration_ms": 0,
                "timestamp": datetime.now(UTC).isoformat(),
            })
            continue

        # Execute Tool safely
        start_time = time.perf_counter()
        tool_instance = tool_map.get(tool_name)
        if not tool_instance:
            output = {"error": f"Tool '{tool_name}' not found"}
        else:
            try:
                output = await tool_instance.ainvoke(tool_args)
            except Exception as exc:  # noqa: BLE001 - tool failures must not stop triage
                logger.warning("Tool execution failed for %s (%s)", tool_name, type(exc).__name__)
                output = {"error": "TOOL_EXECUTION_FAILED"}

        duration_ms = int((time.perf_counter() - start_time) * 1000)
        logger.info("tool_node executed %s in %dms", tool_name, duration_ms)

        tool_outputs.append(ToolMessage(content=json.dumps(output, default=str), tool_call_id=call_id))
        trace.append({
            "step": len(trace) + 1,
            "node": "tool_node",
            "type": TraceStepType.ERROR.value if isinstance(output, dict) and "error" in output else TraceStepType.TOOL_RESULT.value,
            "tool": tool_name,
            "parameters": tool_args,
            "raw_output": output,
            "duration_ms": duration_ms,
            "timestamp": datetime.now(UTC).isoformat(),
        })

    return {
        "messages": tool_outputs,
        "trace": trace,
        "tool_calls_made": tool_calls_made,
    }


async def finalize_node(state: AgentState) -> dict[str, Any]:
    """Generates strictly validated Pydantic TriageResult."""
    trace = list(state.get("trace", []))
    structured_llm = get_finalize_llm()

    finalize_instruction = (
        "Based on all gathered information and conversation history, generate the final customer "
        "response draft, assign the exact tag ('Auto-Resolve' or 'Escalate to Sales'), and state your reasoning."
    )
    prompt_messages = list(state["messages"]) + [HumanMessage(content=finalize_instruction)]

    start_time = time.perf_counter()
    result: TriageResult = await structured_llm.ainvoke(prompt_messages)
    duration_ms = int((time.perf_counter() - start_time) * 1000)

    result = apply_business_rules(state["ticket"], result, trace)

    logger.info("finalize_node completed in %dms | tag=%s", duration_ms, result.tag.value)

    result_dict = result.model_dump()
    trace.append({
        "step": len(trace) + 1,
        "node": "finalize_node",
        "type": TraceStepType.FINAL.value,
        "reasoning": result.reasoning,
        "raw_output": result_dict,
        "duration_ms": duration_ms,
        "timestamp": datetime.now(UTC).isoformat(),
    })

    return {"result": result_dict, "trace": trace}
