"""Security regression tests for graph tool execution limits."""

import asyncio
import json
from typing import Any

import pytest
from langchain_core.messages import AIMessage
from langchain_core.tools import tool

from app.agent import nodes
from app.agent.nodes import agent_node, tool_node
from app.tools.mock_tools import OrderStatusInput


def _tool_call(call_id: str, order_id: str = "ORD-9012") -> dict[str, Any]:
    """Build a model tool call for the order status tool."""
    return {
        "name": "get_order_status",
        "args": {"order_id": order_id},
        "id": call_id,
        "type": "tool_call",
    }


def _tool_state(message: AIMessage, tool_calls_made: int = 0) -> dict[str, Any]:
    """Build the minimal state used by tool_node tests."""
    return {
        "ticket": {"id": "TCK-001", "user_id": "USR-101", "order_id": "ORD-9012", "text": "Where is my order?"},
        "messages": [message],
        "trace": [],
        "tool_calls_made": tool_calls_made,
    }


def test_tool_node_never_exceeds_remaining_call_budget() -> None:
    """A parallel model response cannot execute more than MAX_TOOL_CALLS."""
    message = AIMessage(content="", tool_calls=[
        _tool_call("call-1"), _tool_call("call-2"), _tool_call("call-3"),
    ])

    result = asyncio.run(tool_node(_tool_state(message, tool_calls_made=2)))

    assert result["tool_calls_made"] == 3
    assert sum(step["type"] == "tool_result" for step in result["trace"]) == 1
    assert sum(step["type"] == "error" for step in result["trace"]) == 2
    assert len(result["messages"]) == 3


def test_agent_skips_model_after_tool_budget_is_exhausted(monkeypatch) -> None:
    """The agent proceeds to finalization without another provider request."""
    monkeypatch.setattr(nodes, "get_agent_llm", lambda: pytest.fail("LLM should not be invoked"))
    state = {
        "ticket": {"id": "TCK-001", "user_id": "USR-101", "order_id": "ORD-9012", "text": "Where is my order?"},
        "messages": [], "trace": [], "tool_calls_made": 3,
    }

    result = asyncio.run(agent_node(state))

    assert not result["messages"][-1].tool_calls
    assert "limit" in result["messages"][-1].content.lower()


def test_tool_failure_is_recorded_without_exposing_exception_details(monkeypatch) -> None:
    """Tool failures are trace errors and private exception messages stay server-side."""
    @tool("get_order_status", args_schema=OrderStatusInput)
    async def failing_get_order_status(order_id: str) -> dict[str, str]:
        """Return a shipping lookup result for tests."""
        raise RuntimeError("private diagnostic detail")

    monkeypatch.setattr(nodes, "ALL_TOOLS", [failing_get_order_status])
    state = _tool_state(AIMessage(content="", tool_calls=[_tool_call("call-fail")]))

    result = asyncio.run(tool_node(state))

    assert result["trace"][-1]["type"] == "error"
    assert result["trace"][-1]["raw_output"] == {"error": "TOOL_EXECUTION_FAILED"}
    assert "private diagnostic" not in json.dumps(result["trace"])
    assert "TOOL_EXECUTION_FAILED" in result["messages"][0].content


def test_mismatched_tool_argument_is_rejected_and_traced() -> None:
    """Tool arguments must match the selected ticket metadata."""
    state = _tool_state(AIMessage(content="", tool_calls=[_tool_call("call-mismatch", "ORD-0000")]))

    result = asyncio.run(tool_node(state))

    assert result["trace"][-1]["type"] == "error"
    assert result["trace"][-1]["raw_output"] == {"error": "TOOL_ARGUMENT_REJECTED"}
    assert "TOOL_ARGUMENT_REJECTED" in result["messages"][0].content
