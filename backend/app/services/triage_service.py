"""Coordinates ticket lifecycle and LangGraph triage execution."""

import json
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException

from app.agent.graph import GRAPH_CONFIG, triage_graph
from app.core.logging import logger
from app.schemas.ticket import Ticket, TicketStatus
from app.schemas.triage import TraceStep, TraceStepType, TriageResponse, TriageResult
from app.services.ticket_store import ticket_store


async def run_triage(ticket_id: str) -> TriageResponse:
    """Run a fresh agent triage and persist the resulting ticket status."""
    ticket, started = ticket_store.begin_triage(ticket_id)
    if ticket is None:
        raise HTTPException(404, detail={"error": {"code": "TICKET_NOT_FOUND", "message": "Ticket not found"}})
    if not started:
        raise HTTPException(409, detail={"error": {"code": "TRIAGE_IN_PROGRESS", "message": "Triage is already running"}})

    initial_state: dict[str, Any] = {
        "ticket": ticket.model_dump(mode="json"), "messages": [], "trace": [],
        "tool_calls_made": 0, "result": None, "error": None,
    }
    try:
        state = await triage_graph.ainvoke(initial_state, config=GRAPH_CONFIG)
        result = TriageResult.model_validate(state["result"])
        resolved = ticket_store.update_status(ticket_id, TicketStatus.RESOLVED)
        if resolved is None:
            raise RuntimeError("Ticket disappeared during triage")
        return TriageResponse(ticket=resolved, result=result, trace=state.get("trace", []))
    except Exception as exc:  # noqa: BLE001 - reset ticket state for every failed triage
        ticket_store.update_status(ticket_id, TicketStatus.PENDING)
        logger.error("Triage failed for %s (%s)", ticket_id, type(exc).__name__)
        message = str(exc).upper()
        rate_limited = "429" in message or "RATE_LIMIT" in message or "RESOURCE_EXHAUSTED" in message
        code = "LLM_RATE_LIMITED" if rate_limited else "LLM_UNAVAILABLE"
        status_code = 503 if rate_limited else 502
        trace = [
            {"step": 1, "node": "triage_service", "type": TraceStepType.ERROR.value,
             "raw_output": {"error": code}, "reasoning": "Triage could not be completed.",
             "duration_ms": 0, "timestamp": datetime.now(UTC).isoformat()}
        ]
        raise HTTPException(status_code, detail={
            "error": {"code": code, "message": "The AI service is temporarily unavailable."},
            "trace": trace,
        }) from None


def begin_triage_stream(ticket_id: str) -> AsyncIterator[str]:
    """Reserve a ticket before opening the SSE response so conflicts stay HTTP errors."""
    ticket, started = ticket_store.begin_triage(ticket_id)
    if ticket is None:
        raise HTTPException(404, detail={"error": {"code": "TICKET_NOT_FOUND", "message": "Ticket not found"}})
    if not started:
        raise HTTPException(409, detail={"error": {"code": "TRIAGE_IN_PROGRESS", "message": "Triage is already running"}})
    return _stream_triage(ticket_id, ticket)


def _sse(event: str, payload: Any) -> str:
    """Serialize one safely encoded Server-Sent Event."""
    data = json.dumps(payload, separators=(",", ":"), default=str)
    return f"event: {event}\ndata: {data}\n\n"


async def _stream_triage(ticket_id: str, ticket: Ticket) -> AsyncIterator[str]:
    """Stream LangGraph trace updates, then result and completion events."""
    initial_state: dict[str, Any] = {
        "ticket": ticket.model_dump(mode="json"), "messages": [], "trace": [],
        "tool_calls_made": 0, "result": None, "error": None,
    }
    state = dict(initial_state)
    sent_steps = 0
    completed = False
    try:
        async for update in triage_graph.astream(initial_state, config=GRAPH_CONFIG, stream_mode="updates"):
            for node_update in update.values():
                state.update(node_update)
                trace = node_update.get("trace", [])
                while sent_steps < len(trace):
                    step = TraceStep.model_validate(trace[sent_steps]).model_dump(mode="json")
                    sent_steps += 1
                    yield _sse("trace", step)

        result = TriageResult.model_validate(state["result"])
        resolved = ticket_store.update_status(ticket_id, TicketStatus.RESOLVED)
        if resolved is None:
            raise RuntimeError("Ticket disappeared during triage")
        completed = True
        yield _sse("result", result.model_dump(mode="json"))
        yield _sse("done", {"ticket": resolved.model_dump(mode="json")})
    except Exception as exc:  # noqa: BLE001 - reset ticket state for every failed triage
        ticket_store.update_status(ticket_id, TicketStatus.PENDING)
        logger.error("Streaming triage failed for %s (%s)", ticket_id, type(exc).__name__)
        message = str(exc).upper()
        rate_limited = "429" in message or "RATE_LIMIT" in message or "RESOURCE_EXHAUSTED" in message
        code = "LLM_RATE_LIMITED" if rate_limited else "LLM_UNAVAILABLE"
        trace = state.get("trace", [])
        if sent_steps == len(trace):
            trace = [*trace, {
                "step": len(trace) + 1, "node": "triage_service", "type": TraceStepType.ERROR.value,
                "raw_output": {"error": code}, "reasoning": "Triage could not be completed.",
                "duration_ms": 0, "timestamp": datetime.now(UTC).isoformat(),
            }]
            yield _sse("trace", TraceStep.model_validate(trace[-1]).model_dump(mode="json"))
        yield _sse("error", {
            "error": {"code": code, "message": "The AI service is temporarily unavailable."},
        })
    finally:
        if not completed:
            ticket_store.update_status(ticket_id, TicketStatus.PENDING)
