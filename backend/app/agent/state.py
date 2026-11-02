"""Agent state definition for LangGraph."""

from typing import Annotated, Any

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class AgentState(TypedDict):
    """State schema for the TriageForge LangGraph agent."""

    ticket: dict[str, Any]
    messages: Annotated[list[BaseMessage], add_messages]
    trace: list[dict[str, Any]]
    tool_calls_made: int
    result: dict[str, Any] | None
    error: str | None