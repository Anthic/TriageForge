"""API routes for ticket querying."""

from fastapi import APIRouter, HTTPException, Path, status

from app.schemas.ticket import Ticket
from app.services.ticket_store import ticket_store

router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.get("", response_model=list[Ticket], summary="List all tickets")
async def list_tickets() -> list[Ticket]:
    """Retrieve all tickets currently in the system."""
    return ticket_store.list_all()


@router.get(
    "/{ticket_id}",
    response_model=Ticket,
    summary="Get single ticket by ID",
    responses={
        404: {
            "description": "Ticket not found",
            "content": {"application/json": {"example": {"error": {"code": "TICKET_NOT_FOUND", "message": "Ticket TCK-999 not found"}}}},
        }
    },
)
async def get_ticket(
    ticket_id: str = Path(..., pattern=r"^TCK-\d{3}$", description="Ticket ID e.g. TCK-001"),
) -> Ticket:
    """Fetch ticket details by ticket ID. Raises 404 if not found."""
    ticket = ticket_store.get_by_id(ticket_id)
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "TICKET_NOT_FOUND", "message": f"Ticket {ticket_id} not found"}},
        )
    return ticket