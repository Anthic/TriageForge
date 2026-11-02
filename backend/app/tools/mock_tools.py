"""Mock helper tools with strict Pydantic schemas for autonomous agent execution."""

from typing import Any

from langchain_core.tools import tool
from pydantic import BaseModel, Field


class OrderStatusInput(BaseModel):
    """Input schema for checking order delivery status."""

    order_id: str = Field(
        ...,
        pattern=r"^ORD-\d+$",
        description="The unique order identifier formatted as ORD-XXXX, e.g. ORD-9012",
    )


class UserTierInput(BaseModel):
    """Input schema for checking user subscription tier."""

    user_id: str = Field(
        ...,
        pattern=r"^USR-\d+$",
        description="The unique user identifier formatted as USR-XXXX, e.g. USR-101",
    )


@tool(args_schema=OrderStatusInput)
def get_order_status(order_id: str) -> dict[str, Any]:
    """Retrieve shipping status and estimated delivery date for a specific order.

    Use this tool ONLY when a customer asks about order tracking, delivery ETA,
    or shipping status, and an order ID is present.
    """
    return {
        "order_id": order_id,
        "status": "In Transit",
        "est_delivery": "Tomorrow",
    }


@tool(args_schema=UserTierInput)
def get_user_tier(user_id: str) -> dict[str, Any]:
    """Retrieve subscription tier and upgrade eligibility for a specific customer.

    Use this tool ONLY when a customer asks about plan upgrades, account tiers,
    or Enterprise subscription eligibility.
    """
    return {
        "user_id": user_id,
        "current_tier": "Free",
        "eligible_for_upgrade": True,
    }


# Export list of tools for LangGraph binding
ALL_TOOLS = [get_order_status, get_user_tier]
