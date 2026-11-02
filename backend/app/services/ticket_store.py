"""In-memory ticket storage and lifecycle state management."""

from threading import Lock

from app.data.seed import SEED_TICKETS
from app.schemas.ticket import Ticket, TicketStatus


class TicketStore:
    """Thread-safe in-memory store for support tickets."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._tickets: dict[str, Ticket] = {}
        self.reset_to_seed()

    def reset_to_seed(self) -> None:
        """Reloads the exact seed tickets into memory."""
        with self._lock:
            self._tickets = {ticket.id: ticket.model_copy(deep=True) for ticket in SEED_TICKETS}

    def list_all(self) -> list[Ticket]:
        """Returns all tickets ordered by ID."""
        with self._lock:
            return sorted(self._tickets.values(), key=lambda t: t.id)

    def get_by_id(self, ticket_id: str) -> Ticket | None:
        """Retrieves a single ticket by its ID."""
        with self._lock:
            ticket = self._tickets.get(ticket_id)
            return ticket.model_copy(deep=True) if ticket else None

    def update_status(self, ticket_id: str, new_status: TicketStatus) -> Ticket | None:
        """Safely updates a ticket's status and returns the updated entity."""
        with self._lock:
            ticket = self._tickets.get(ticket_id)
            if not ticket:
                return None
            updated = ticket.model_copy(update={"status": new_status})
            self._tickets[ticket_id] = updated
            return updated.model_copy(deep=True)

    def begin_triage(self, ticket_id: str) -> tuple[Ticket | None, bool]:
        """Atomically move a ticket into Processing unless it is already processing."""
        with self._lock:
            ticket = self._tickets.get(ticket_id)
            if ticket is None:
                return None, False
            if ticket.status == TicketStatus.PROCESSING:
                return ticket.model_copy(deep=True), False
            updated = ticket.model_copy(update={"status": TicketStatus.PROCESSING})
            self._tickets[ticket_id] = updated
            return updated.model_copy(deep=True), True


# Global singleton instance
ticket_store = TicketStore()
