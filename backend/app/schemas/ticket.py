"""Pydantic schemas and enums for support tickets."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class TicketStatus(str, Enum):
    """Lifecycle status of a support ticket."""

    PENDING = "Pending"
    PROCESSING = "Processing"
    RESOLVED = "Resolved"


class Ticket(BaseModel):
    """Support ticket entity schema."""

    id: str = Field(
        ...,
        pattern=r"^TCK-\d{3}$",
        description="Ticket unique ID, formatted as TCK-XXX",
        examples=["TCK-001"],
    )
    user_id: str = Field(
        ...,
        pattern=r"^USR-\d+$",
        description="Customer user ID, formatted as USR-XXX",
        examples=["USR-101"],
    )
    order_id: str | None = Field(
        default=None,
        pattern=r"^ORD-\d+$",
        description="Order ID if related to a physical order",
        examples=["ORD-9012"],
    )
    text: str = Field(
        ...,
        min_length=5,
        description="Original support ticket message submitted by customer",
    )
    status: TicketStatus = Field(
        default=TicketStatus.PENDING,
        description="Current ticket status",
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp of ticket creation",
    )