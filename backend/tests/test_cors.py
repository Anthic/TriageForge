"""Tests for CORS policy across localhost and Vercel domains."""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_cors_allows_localhost_3000() -> None:
    """Frontend dev server on port 3000 must be allowed."""
    response = client.get("/health", headers={"Origin": "http://localhost:3000"})
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"
    assert response.headers.get("access-control-allow-credentials") == "true"


def test_cors_allows_localhost_3001() -> None:
    """Alternative dev server on port 3001 must be allowed."""
    response = client.get("/health", headers={"Origin": "http://localhost:3001"})
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3001"
    assert response.headers.get("access-control-allow-credentials") == "true"


def test_cors_allows_127_0_0_1() -> None:
    """Direct IP loopback origins on 3000 and 3001 must be allowed."""
    for origin in ("http://127.0.0.1:3000", "http://127.0.0.1:3001"):
        response = client.get("/health", headers={"Origin": origin})
        assert response.status_code == 200
        assert response.headers.get("access-control-allow-origin") == origin


def test_cors_allows_vercel_production_and_preview_domains() -> None:
    """Any Vercel production or preview branch origin must be allowed via regex."""
    vercel_origins = [
        "https://triageforge.vercel.app",
        "https://triageforge-git-main-user.vercel.app",
        "https://frontend-alpha-preview.vercel.app",
    ]
    for origin in vercel_origins:
        response = client.get("/health", headers={"Origin": origin})
        assert response.status_code == 200
        assert response.headers.get("access-control-allow-origin") == origin
        assert response.headers.get("access-control-allow-credentials") == "true"


def test_cors_preflight_options_for_stream() -> None:
    """Preflight OPTIONS request from Vercel must succeed with 200 OK."""
    headers = {
        "Origin": "https://triageforge.vercel.app",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "Content-Type,Accept",
    }
    response = client.options("/tickets/TCK-001/triage/stream", headers=headers)
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "https://triageforge.vercel.app"
    assert response.headers.get("access-control-allow-credentials") == "true"
    assert "POST" in response.headers.get("access-control-allow-methods", "")


def test_cors_blocks_unauthorized_external_origins() -> None:
    """Random unauthorized domains must not receive access control headers."""
    response = client.get("/health", headers={"Origin": "https://malicious-phishing-site.com"})
    assert response.status_code == 200
    assert "access-control-allow-origin" not in response.headers
