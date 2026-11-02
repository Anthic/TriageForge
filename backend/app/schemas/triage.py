"""Pydantic schemas for agent triage output and execution trace logging."""

from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator

from app.schemas.ticket import Ticket


class ResolutionTag(str, Enum):
    """Permitted resolution action tags."""

    AUTO_RESOLVE = "Auto-Resolve"
    ESCALATE_TO_SALES = "Escalate to Sales"


class TraceStepType(str, Enum):
    """Categorization of an execution trace event."""

    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    REASONING = "reasoning"
    FINAL = "final"
    ERROR = "error"


class TraceStep(BaseModel):
    """Audit log entry capturing a single step in agent execution."""

    step: int = Field(..., description="1-indexed step sequence number")
    node: str = Field(..., description="LangGraph node name that produced this trace")
    type: TraceStepType = Field(..., description="Category of the event")
    tool: str | None = Field(default=None, description="Name of tool if invoked")
    parameters: dict[str, Any] | None = Field(default=None, description="Arguments sent to tool")
    raw_output: Any | None = Field(default=None, description="Raw returned value from tool")
    reasoning: str | None = Field(default=None, description="Agent thought process or explanation")
    duration_ms: int = Field(default=0, description="Execution time in milliseconds")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat(),
        description="ISO-8601 UTC timestamp",
    )


class TriageResult(BaseModel):
    """Strict structured output required from the finalize node."""

    draft: str = Field(
        ...,
        description="Polite, factual, customer-facing response draft under 120 words.",
    )
    tag: ResolutionTag = Field(
        ...,
        description="Action classification: Auto-Resolve or Escalate to Sales.",
    )
    reasoning: str = Field(
        ...,
        description="Clear internal explanation for why this draft and tag were selected.",
    )

    @field_validator("draft")
    @classmethod
    def validate_draft_word_count(cls, value: str) -> str:
        """Keep customer replies within the product's approximate 120-word limit."""
        if len(value.split()) > 120:
            raise ValueError("Customer response draft must not exceed 120 words")
        return value


class TriageResponse(BaseModel):
    """Complete API response returned by the triage endpoint."""

    ticket: Ticket
    result: TriageResult
    trace: list[TraceStep]
