"""Default seed tickets as specified in project requirements."""

from datetime import datetime, timezone
from app.schemas.ticket import Ticket, TicketStatus


SEED_TICKETS: list[Ticket] = [
    Ticket(
        id="TCK-001",
        user_id="USR-101",
        order_id="ORD-9012",
        text="Where is my package #ORD-9012? It was supposed to arrive yesterday.",
        status=TicketStatus.PENDING,
        created_at=datetime(2026, 11, 1, 9, 0, 0, tzinfo=timezone.utc),
    ),
    Ticket(
        id="TCK-002",
        user_id="USR-204",
        order_id=None,
        text="Can you upgrade my account to Enterprise tier?",
        status=TicketStatus.PENDING,
        created_at=datetime(2026, 11, 1, 10, 15, 0, tzinfo=timezone.utc),
    ),
    Ticket(
        id="TCK-003",
        user_id="USR-309",
        order_id=None,
        text="How do I update my profile picture?",
        status=TicketStatus.PENDING,
        created_at=datetime(2026, 11, 1, 11, 30, 0, tzinfo=timezone.utc),
    ),
]