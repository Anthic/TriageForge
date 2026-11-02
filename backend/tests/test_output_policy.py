"""Tests for deterministic, fact-grounded customer drafts."""

import pytest
from pydantic import ValidationError

from app.agent.output_policy import apply_business_rules
from app.schemas.triage import ResolutionTag, TriageResult


def _model_result() -> TriageResult:
    return TriageResult(
        draft="Our team will contact you at invented@example.com tomorrow.",
        tag=ResolutionTag.AUTO_RESOLVE,
        reasoning="Model generated draft.",
    )


def test_order_draft_uses_only_order_tool_facts() -> None:
    trace = [{
        "type": "tool_result", "tool": "get_order_status",
        "raw_output": {"order_id": "ORD-9012", "status": "In Transit", "est_delivery": "Tomorrow"},
    }]

    result = apply_business_rules({"text": "Where is my package?", "order_id": "ORD-9012"}, _model_result(), trace)

    assert result.draft == (
        "Hi there,\n\nI’m sorry your order hasn’t arrived as expected. I checked order ORD-9012, "
        "and it is currently in transit. The estimated delivery is tomorrow.\n\n"
        "If it hasn’t arrived by then, please let us know.\n\nBest,\nSupport Team"
    )
    assert result.tag == ResolutionTag.AUTO_RESOLVE
    assert "invented" not in result.draft


def test_upgrade_draft_does_not_promise_sales_follow_up() -> None:
    trace = [{
        "type": "tool_result", "tool": "get_user_tier",
        "raw_output": {"user_id": "USR-204", "current_tier": "Free", "eligible_for_upgrade": True},
    }]

    result = apply_business_rules({"text": "Upgrade to Enterprise"}, _model_result(), trace)

    assert "Free" in result.draft
    assert "eligible" in result.draft
    assert "Please contact Sales to continue." in result.draft
    assert result.draft.startswith("Hi there,\n\nI checked your account.")
    assert result.draft.endswith("Best,\nSupport Team")
    assert "contact you" not in result.draft
    assert "invented@example.com" not in result.draft
    assert result.tag == ResolutionTag.ESCALATE_TO_SALES


def test_profile_picture_draft_avoids_unverified_product_details() -> None:
    result = apply_business_rules(
        {"text": "How do I update my profile picture?"}, _model_result(), []
    )

    assert "profile or account settings" in result.draft
    assert "MB" not in result.draft
    assert "minutes" not in result.draft
    assert "top-right" not in result.draft
    assert "tomorrow" not in result.draft
    assert result.draft.startswith("Hi there,\n\n")
    assert result.draft.endswith("Best,\nSupport Team")
    assert result.tag == ResolutionTag.AUTO_RESOLVE


def test_tool_error_cannot_leak_unverified_order_claims() -> None:
    result = apply_business_rules(
        {"text": "Where is my package?", "order_id": "ORD-9012"},
        _model_result(),
        [{"type": "error", "tool": "get_order_status", "raw_output": {"error": "TOOL_EXECUTION_FAILED"}}],
    )

    assert result.draft.startswith("Hi there,\n\nI’m sorry, but I couldn’t verify your order status")
    assert result.draft.endswith("Best,\nSupport Team")
    assert result.tag == ResolutionTag.AUTO_RESOLVE


def test_customer_draft_is_limited_to_120_words() -> None:
    accepted = TriageResult(draft="word " * 120, tag=ResolutionTag.AUTO_RESOLVE, reasoning="Valid.")
    assert len(accepted.draft.split()) == 120
    with pytest.raises(ValidationError):
        TriageResult(draft="word " * 121, tag=ResolutionTag.AUTO_RESOLVE, reasoning="Too long.")
