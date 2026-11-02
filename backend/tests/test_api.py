"""API tests for ticket triage responses and lifecycle handling."""

from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.ticket import TicketStatus
from app.services.ticket_store import ticket_store

client = TestClient(app)


def test_ticket_route_maps_invalid_id_to_validation_error() -> None:
    """Malformed ticket IDs return the documented validation envelope."""
    response = client.get("/tickets/not-a-ticket")

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_ticket_route_returns_not_found_for_unknown_ticket() -> None:
    """Well-formed unknown ticket IDs return the documented not-found code."""
    response = client.get("/tickets/TCK-999")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "TICKET_NOT_FOUND"


def test_triage_route_maps_invalid_id_to_validation_error() -> None:
    """Malformed triage IDs use the same structured validation envelope."""
    response = client.post("/tickets/invalid/triage")

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_triage_unknown_ticket_returns_not_found() -> None:
    """A well-formed ID missing from the store is handled before agent execution."""
    response = client.post("/tickets/TCK-999/triage")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "TICKET_NOT_FOUND"


def test_triage_endpoint_returns_structured_result_and_trace(monkeypatch) -> None:
    """The API returns validated result data and marks successful tickets resolved."""
    ticket_store.reset_to_seed()
    graph = AsyncMock(return_value={
        "result": {"draft": "Your order is in transit and is expected tomorrow.",
                   "tag": "Auto-Resolve", "reasoning": "Order status was checked."},
        "trace": [{"step": 1, "node": "finalize_node", "type": "final"}],
    })
    monkeypatch.setattr("app.services.triage_service.triage_graph.ainvoke", graph)

    response = client.post("/tickets/TCK-001/triage")

    assert response.status_code == 200
    assert response.json()["result"]["tag"] == "Auto-Resolve"
    assert response.json()["trace"][0]["type"] == "final"
    assert response.json()["ticket"]["status"] == "Resolved"


def test_triage_rejects_concurrent_request() -> None:
    """A second run for a Processing ticket returns the documented conflict."""
    ticket_store.reset_to_seed()
    ticket_store.update_status("TCK-001", TicketStatus.PROCESSING)

    response = client.post("/tickets/TCK-001/triage")

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "TRIAGE_IN_PROGRESS"


def test_triage_provider_failure_resets_status_and_returns_trace(monkeypatch) -> None:
    """Provider errors are sanitized and leave the ticket available for retry."""
    ticket_store.reset_to_seed()
    graph = AsyncMock(side_effect=RuntimeError("provider failure with sensitive details"))
    monkeypatch.setattr("app.services.triage_service.triage_graph.ainvoke", graph)

    response = client.post("/tickets/TCK-001/triage")

    assert response.status_code == 502
    assert response.json()["error"]["code"] == "LLM_UNAVAILABLE"
    assert "sensitive" not in response.text
    assert response.json()["trace"][0]["type"] == "error"
    assert ticket_store.get_by_id("TCK-001").status == TicketStatus.PENDING


def test_triage_provider_rate_limit_maps_to_service_unavailable(monkeypatch) -> None:
    """Provider 429 errors map to the documented 503 response with trace."""
    ticket_store.reset_to_seed()
    graph = AsyncMock(side_effect=RuntimeError("Groq request failed with status 429"))
    monkeypatch.setattr("app.services.triage_service.triage_graph.ainvoke", graph)

    response = client.post("/tickets/TCK-001/triage")

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "LLM_RATE_LIMITED"
    assert response.json()["trace"][0]["type"] == "error"
    assert ticket_store.get_by_id("TCK-001").status == TicketStatus.PENDING
