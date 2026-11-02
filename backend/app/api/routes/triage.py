"""Ticket triage endpoint."""

from fastapi import APIRouter, Path, Request

from app.core.config import settings
from app.core.rate_limit import limiter
from app.schemas.triage import TriageResponse
from app.services.triage_service import run_triage

router = APIRouter(prefix="/tickets", tags=["triage"])


@router.post("/{ticket_id}/triage", response_model=TriageResponse)
@limiter.limit(lambda: f"{settings.triage_requests_per_minute}/minute")
async def triage_ticket(
    request: Request,
    ticket_id: str = Path(..., pattern=r"^TCK-\d{3}$", description="Ticket ID e.g. TCK-001"),
) -> TriageResponse:
    """Run the support agent for a ticket and return result with execution trace."""
    return await run_triage(ticket_id)
