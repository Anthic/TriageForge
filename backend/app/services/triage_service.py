"""Coordinates ticket lifecycle and LangGraph triage execution."""

from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException

from app.agent.graph import GRAPH_CONFIG, triage_graph
from app.core.logging import logger
from app.schemas.ticket import TicketStatus
from app.schemas.triage import TraceStepType, TriageResponse
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
        from app.schemas.triage import TriageResult
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
