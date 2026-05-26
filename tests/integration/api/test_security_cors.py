"""Integration tests for CORS configuration (FR-045)."""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from rapidcull.security import Settings, configure_app


def _make_app(settings: Settings) -> FastAPI:
    """Build a minimal test app with given settings applied."""
    test_app = FastAPI()

    @test_app.get("/test/read")
    def read() -> dict[str, bool]:
        return {"ok": True}

    @test_app.post("/test/mutate")
    def mutate() -> dict[str, bool]:
        return {"ok": True}

    configure_app(test_app, settings=settings)
    return test_app


@pytest.fixture()
def localhost_client() -> TestClient:
    settings = Settings(mode="localhost")
    return TestClient(_make_app(settings), raise_server_exceptions=False)


@pytest.fixture()
def lan_client() -> TestClient:
    settings = Settings(
        mode="lan",
        auth_token="secret",
        allowed_origins=["http://example.com"],
    )
    return TestClient(_make_app(settings), raise_server_exceptions=False)


class TestLocalhostCors:
    def test_localhost_origin_allowed(self, localhost_client: TestClient) -> None:
        response = localhost_client.get("/test/read", headers={"Origin": "http://localhost"})
        assert response.headers.get("access-control-allow-origin") == "http://localhost"

    def test_127_origin_allowed(self, localhost_client: TestClient) -> None:
        response = localhost_client.get("/test/read", headers={"Origin": "http://127.0.0.1"})
        assert response.headers.get("access-control-allow-origin") == "http://127.0.0.1"


class TestLanCors:
    def test_explicit_origin_reflected(self, lan_client: TestClient) -> None:
        response = lan_client.get(
            "/test/read",
            headers={"Origin": "http://example.com"},
        )
        assert response.headers.get("access-control-allow-origin") == "http://example.com"

    def test_unlisted_origin_not_reflected(self, lan_client: TestClient) -> None:
        response = lan_client.get(
            "/test/read",
            headers={"Origin": "http://evil.com"},
        )
        acao = response.headers.get("access-control-allow-origin")
        assert acao != "http://evil.com"
        assert acao != "*"

    def test_no_wildcard_in_lan_mode(self, lan_client: TestClient) -> None:
        """LAN mode must never use wildcard CORS origin."""
        response = lan_client.get(
            "/test/read",
            headers={"Origin": "http://example.com"},
        )
        assert response.headers.get("access-control-allow-origin") != "*"
