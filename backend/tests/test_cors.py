"""Tests for CORS configuration parsing and Vercel regex matching."""

import re
from app.core.config import Settings, settings


def test_default_cors_origins_includes_localhost_ports() -> None:
    """Default origins must include local ports 3000 and 3001 for both localhost and 127.0.0.1."""
    origins = settings.cors_origins_list
    assert "http://localhost:3000" in origins
    assert "http://localhost:3001" in origins
    assert "http://127.0.0.1:3000" in origins
    assert "http://127.0.0.1:3001" in origins


def test_cors_origins_strips_trailing_slashes_and_whitespace() -> None:
    """Custom origins in .env must be normalized without trailing slashes."""
    custom_settings = Settings(
        cors_origins="http://localhost:3000/ , https://my-frontend.vercel.app/ "
    )
    assert custom_settings.cors_origins_list == [
        "http://localhost:3000",
        "https://my-frontend.vercel.app",
    ]


def test_cors_regex_matches_vercel_domains() -> None:
    """The regex must match production and preview Vercel domains."""
    assert settings.cors_origin_regex is not None
    pattern = re.compile(settings.cors_origin_regex)
    assert pattern.match("https://triageforge.vercel.app")
    assert pattern.match("https://triageforge-git-main-user.vercel.app")
    assert pattern.match("https://preview-12345.vercel.app")


def test_cors_regex_rejects_unauthorized_domains() -> None:
    """The regex must reject non-vercel domains and unencrypted http."""
    assert settings.cors_origin_regex is not None
    pattern = re.compile(settings.cors_origin_regex)
    assert not pattern.match("http://triageforge.vercel.app")
    assert not pattern.match("https://malicious-vercel.app.attacker.com")
    assert not pattern.match("https://attacker.com")

