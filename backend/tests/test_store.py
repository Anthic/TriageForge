"""Unit tests for in-memory TicketStore operations and status lifecycle."""

from app.schemas.ticket import TicketStatus
from app.services.ticket_store import ticket_store


def test_ticket_store_loads_exact_seed_tickets() -> None:
    """Verify store initializes with exactly 3 seed tickets."""
    ticket_store.reset_to_seed()
    tickets = ticket_store.list_all()
    assert len(tickets) == 3
    assert [t.id for t in tickets] == ["TCK-001", "TCK-002", "TCK-003"]


def test_ticket_store_status_transition() -> None:
    """Verify ticket status transitions from Pending to Processing to Resolved."""
    ticket_store.reset_to_seed()

    # Transition to Processing
    updated = ticket_store.update_status("TCK-001", TicketStatus.PROCESSING)
    assert updated is not None
    assert updated.status == TicketStatus.PROCESSING

    # Transition to Resolved
    resolved = ticket_store.update_status("TCK-001", TicketStatus.RESOLVED)
    assert resolved is not None
    assert resolved.status == TicketStatus.RESOLVED


def test_ticket_store_get_unknown_returns_none() -> None:
    """Verify non-existent ticket query returns None."""
    assert ticket_store.get_by_id("TCK-999") is None
