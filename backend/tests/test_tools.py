"""Unit tests for mock tools and input schema validation."""

import pytest
from pydantic import ValidationError

from app.tools.mock_tools import (
    OrderStatusInput,
    UserTierInput,
    get_order_status,
    get_user_tier,
)


def test_get_order_status_returns_spec_output() -> None:
    """Verify get_order_status returns the exact spec output."""
    result = get_order_status.invoke({"order_id": "ORD-9012"})
    assert result == {
        "order_id": "ORD-9012",
        "status": "In Transit",
        "est_delivery": "Tomorrow",
    }


def test_get_user_tier_returns_spec_output() -> None:
    """Verify get_user_tier returns the exact spec output."""
    result = get_user_tier.invoke({"user_id": "USR-204"})
    assert result == {
        "user_id": "USR-204",
        "current_tier": "Free",
        "eligible_for_upgrade": True,
    }


def test_order_status_rejects_invalid_id() -> None:
    """Verify regex rejects non-standard order IDs."""
    with pytest.raises(ValidationError):
        OrderStatusInput(order_id="INVALID_123")


def test_user_tier_rejects_invalid_id() -> None:
    """Verify regex rejects non-standard user IDs."""
    with pytest.raises(ValidationError):
        UserTierInput(user_id="INVALID_USER")