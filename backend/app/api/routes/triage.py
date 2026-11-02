"""Ticket triage endpoint."""

from fastapi import APIRouter, Path, Request
from fastapi.responses import StreamingResponse

from app.core.config import settings
from app.core.rate_limit import limiter
from app.schemas.triage import TriageResponse
from app.services.triage_service import begin_triage_stream, run_triage

router = APIRouter(prefix="/tickets", tags=["triage"])


@router.post("/{ticket_id}/triage", response_model=TriageResponse)
@limiter.limit(lambda: f"{settings.triage_requests_per_minute}/minute")
async def triage_ticket(
    request: Request,
    ticket_id: str = Path(..., pattern=r"^TCK-\d{3}$", description="Ticket ID e.g. TCK-001"),
) -> TriageResponse:
    """Run the support agent for a ticket and return result with execution trace."""
    return await run_triage(ticket_id)


@router.post("/{ticket_id}/triage/stream")
@limiter.limit(lambda: f"{settings.triage_requests_per_minute}/minute")
async def triage_ticket_stream(
    request: Request,
    ticket_id: str = Path(..., pattern=r"^TCK-\d{3}$", description="Ticket ID e.g. TCK-001"),
) -> StreamingResponse:
    """Stream each agent trace step using Server-Sent Events over a POST request."""
    event_stream = begin_triage_stream(ticket_id)
    return StreamingResponse(
        event_stream,
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache, no-transform", "X-Accel-Buffering": "no"},
    )
