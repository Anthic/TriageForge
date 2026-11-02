"""Apply deterministic business rules to customer-facing drafts."""

from typing import Any

from app.schemas.triage import ResolutionTag, TriageResult


def _successful_tool_result(trace: list[dict[str, Any]], tool_name: str) -> dict[str, Any] | None:
    """Return the latest successful result for a named tool, if present."""
    for step in reversed(trace):
        output = step.get("raw_output")
        if (
            step.get("type") == "tool_result"
            and step.get("tool") == tool_name
            and isinstance(output, dict)
            and "error" not in output
        ):
            return output
    return None


def _ticket_text(ticket: dict[str, Any]) -> str:
    """Normalize customer text for deterministic business-rule matching."""
    return str(ticket.get("text", "")).casefold()


def _tool_failed(trace: list[dict[str, Any]], tool_name: str) -> bool:
    """Return whether a named tool was rejected or failed during this run."""
    return any(
        step.get("type") == "error" and step.get("tool") == tool_name
        for step in trace
    )


def apply_business_rules(
    ticket: dict[str, Any], result: TriageResult, trace: list[dict[str, Any]]
) -> TriageResult:
    """Ground required product scenarios in tool data or approved generic guidance."""
    order = _successful_tool_result(trace, "get_order_status")
    if order:
        order_id = order.get("order_id")
        status = order.get("status")
        eta = order.get("est_delivery")
        if order_id is None or status is None or eta is None:
            return TriageResult(
                draft="We could not verify the order status. Please try again later.",
                tag=ResolutionTag.AUTO_RESOLVE,
                reasoning="The order status tool did not return all required fields.",
            )
        draft = f"Your order {order_id} is currently {status}. Estimated delivery: {eta}."
        return TriageResult(draft=draft, tag=ResolutionTag.AUTO_RESOLVE,
                            reasoning="Order status and estimated delivery are taken from the order status tool.")

    tier = _successful_tool_result(trace, "get_user_tier")
    if tier:
        current_tier = tier.get("current_tier")
        if current_tier is None:
            return TriageResult(
                draft="We could not verify your current plan. Please contact Sales to discuss Enterprise upgrade options.",
                tag=ResolutionTag.ESCALATE_TO_SALES,
                reasoning="The user tier tool did not return the current plan.",
            )
        eligibility = (
            "You are eligible for an upgrade. "
            if tier.get("eligible_for_upgrade") is True
            else ""
        )
        draft = (
            f"Your current plan is {current_tier}. {eligibility}"
            "Please contact our Sales team to discuss Enterprise upgrade options."
        )
        return TriageResult(draft=draft, tag=ResolutionTag.ESCALATE_TO_SALES,
                            reasoning="The user tier came from the tier tool; Enterprise upgrades are handled by Sales.")

    if _tool_failed(trace, "get_order_status"):
        return TriageResult(
            draft="We could not verify your order status. Please try again later.",
            tag=ResolutionTag.AUTO_RESOLVE,
            reasoning="The order status tool did not complete successfully.",
        )

    if _tool_failed(trace, "get_user_tier"):
        return TriageResult(
            draft="We could not verify your current plan. Please contact Sales to discuss Enterprise upgrade options.",
            tag=ResolutionTag.ESCALATE_TO_SALES,
            reasoning="The user tier tool did not complete successfully.",
        )

    text = _ticket_text(ticket)
    if (
        any(term in text for term in ("where is my", "shipping", "delivery", "tracking", "track my", "package"))
        and not ticket.get("order_id")
    ):
        return TriageResult(
            draft="Could you share your order ID so we can check its shipping status?",
            tag=ResolutionTag.AUTO_RESOLVE,
            reasoning="An order ID is required before the order status tool can be used.",
        )

    if any(term in text for term in ("upgrade", "enterprise", "tier", "plan")):
        return TriageResult(
            draft="Enterprise upgrades are handled by our Sales team. Please contact Sales to discuss next steps.",
            tag=ResolutionTag.ESCALATE_TO_SALES,
            reasoning="Enterprise upgrade requests are handled by Sales.",
        )

    if any(term in text for term in ("profile picture", "profile photo", "avatar")):
        return TriageResult(
            draft=("You can usually change your profile picture from your profile or account settings. "
                   "Look for the profile photo option, choose a new image, and save your changes. "
                   "If you cannot find the option, contact support for guidance."),
            tag=ResolutionTag.AUTO_RESOLVE,
            reasoning="This is a general self-service question and does not require a support tool.",
        )

    return result
