"""Graph definition and conditional edge wiring for TriageForge."""

from typing import Literal

from langgraph.graph import END, START, StateGraph

from app.agent.nodes import agent_node, finalize_node, tool_node
from app.agent.state import AgentState
from app.core.config import settings


def route_after_agent(state: AgentState) -> Literal["tools", "finalize"]:
    """Conditional routing edge determining whether to run tools or finalize."""
    messages = state.get("messages", [])
    if not messages:
        return "finalize"

    last_message = messages[-1]
    has_tool_calls = bool(getattr(last_message, "tool_calls", None))
    tool_calls_made = state.get("tool_calls_made", 0)

    if has_tool_calls and tool_calls_made < settings.max_tool_calls:
        return "tools"
    return "finalize"


def build_triage_graph():
    """Builds and compiles the StateGraph workflow with retry policies."""
    workflow = StateGraph(AgentState)

    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", tool_node)
    workflow.add_node("finalize", finalize_node)

    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges(
        "agent",
        route_after_agent,
        {"tools": "tools", "finalize": "finalize"},
    )
    workflow.add_edge("tools", "agent")
    workflow.add_edge("finalize", END)

    return workflow.compile()


# Global compiled graph instance
triage_graph = build_triage_graph()

# Recursion limit passed at invocation time via config
GRAPH_CONFIG = {"recursion_limit": (settings.max_tool_calls * 2) + 2}
