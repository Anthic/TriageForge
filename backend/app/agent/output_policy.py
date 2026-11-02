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
                draft=("Hi there,\n\nI’m sorry, but I couldn’t verify your order status just now. "
                       "Please try again shortly.\n\nBest,\nSupport Team"),
                tag=ResolutionTag.AUTO_RESOLVE,
                reasoning="The order status tool did not return all required fields.",
            )
        status_text = str(status).lower()
        eta_text = str(eta).lower()
        draft = (
            "Hi there,\n\n"
            f"I’m sorry your order hasn’t arrived as expected. I checked order {order_id}, "
            f"and it is currently {status_text}. The estimated delivery is {eta_text}.\n\n"
            "If it hasn’t arrived by then, please let us know.\n\n"
            "Best,\nSupport Team"
        )
        return TriageResult(draft=draft, tag=ResolutionTag.AUTO_RESOLVE,
                            reasoning="The order lookup confirmed the current status and estimated delivery.")

    tier = _successful_tool_result(trace, "get_user_tier")
    if tier:
        current_tier = tier.get("current_tier")
        if current_tier is None:
            return TriageResult(
                draft=("Hi there,\n\nI couldn’t confirm your current plan. The Sales team handles "
                       "Enterprise upgrades and can discuss the available options with you. "
                       "Please contact Sales to continue.\n\nBest,\nSupport Team"),
                tag=ResolutionTag.ESCALATE_TO_SALES,
                reasoning="The user tier tool did not return the current plan.",
            )
        eligibility = (
            "Your account is eligible for an upgrade. "
            if tier.get("eligible_for_upgrade") is True
            else ""
        )
        draft = (
            "Hi there,\n\n"
            f"I checked your account. You’re on the {current_tier} plan. {eligibility}"
            "The Sales team handles Enterprise upgrades and can discuss the available options with you. "
            "Please contact Sales to continue.\n\n"
            "Best,\nSupport Team"
        )
        return TriageResult(draft=draft, tag=ResolutionTag.ESCALATE_TO_SALES,
                            reasoning="The account plan and upgrade eligibility were checked. Enterprise requests need Sales follow-up.")

    if _tool_failed(trace, "get_order_status"):
        return TriageResult(
            draft=("Hi there,\n\nI’m sorry, but I couldn’t verify your order status just now. "
                   "Please try again shortly.\n\nBest,\nSupport Team"),
            tag=ResolutionTag.AUTO_RESOLVE,
            reasoning="The order status tool did not complete successfully.",
        )

    if _tool_failed(trace, "get_user_tier"):
        return TriageResult(
            draft=("Hi there,\n\nI couldn’t confirm your current plan. The Sales team handles "
                   "Enterprise upgrades and can discuss the available options with you. "
                   "Please contact Sales to continue.\n\nBest,\nSupport Team"),
            tag=ResolutionTag.ESCALATE_TO_SALES,
            reasoning="The user tier tool did not complete successfully.",
        )

    text = _ticket_text(ticket)
    if (
        any(term in text for term in ("where is my", "shipping", "delivery", "tracking", "track my", "package"))
        and not ticket.get("order_id")
    ):
        return TriageResult(
            draft=("Hi there,\n\nI’d be happy to check the delivery status for you. "
                   "Could you share your order ID so I can look it up?\n\nBest,\nSupport Team"),
            tag=ResolutionTag.AUTO_RESOLVE,
            reasoning="An order ID is required before the order status tool can be used.",
        )

    if any(term in text for term in ("upgrade", "enterprise", "tier", "plan")):
        return TriageResult(
            draft=("Hi there,\n\nThe Sales team handles Enterprise upgrades and can walk you through "
                   "the available options. Please contact Sales to discuss the next steps.\n\n"
                   "Best,\nSupport Team"),
            tag=ResolutionTag.ESCALATE_TO_SALES,
            reasoning="Enterprise upgrade requests are handled by Sales.",
        )

    if any(term in text for term in ("profile picture", "profile photo", "avatar")):
        return TriageResult(
            draft=("Hi there,\n\nTo update your profile picture, open your profile or account settings "
                   "and look for the photo update option. Choose a new image and save your changes. "
                   "If you can’t find the setting, please contact Support for help.\n\n"
                   "Best,\nSupport Team"),
            tag=ResolutionTag.AUTO_RESOLVE,
            reasoning="This is a general self-service question and does not require a support tool.",
        )

    return result
