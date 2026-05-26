"""Integration tests for authentication middleware (FR-043, FR-044)."""

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

    @test_app.delete("/test/delete")
    def delete() -> dict[str, bool]:
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
        auth_token="test-token",
        allowed_origins=["http://localhost"],
    )
    return TestClient(_make_app(settings), raise_server_exceptions=False)


class TestLocalhostMode:
    """FR-043: In localhost mode, auth is disabled by default."""

    def test_post_no_auth_required(self, localhost_client: TestClient) -> None:
        response = localhost_client.post("/test/mutate")
        assert response.status_code == 200

    def test_delete_no_auth_required(self, localhost_client: TestClient) -> None:
        response = localhost_client.delete("/test/delete")
        assert response.status_code == 200

    def test_get_no_auth_required(self, localhost_client: TestClient) -> None:
        response = localhost_client.get("/test/read")
        assert response.status_code == 200


class TestLanMode:
    """FR-044: In LAN mode, mutating endpoints require Bearer token."""

    def test_post_without_token_returns_401(self, lan_client: TestClient) -> None:
        response = lan_client.post("/test/mutate")
        assert response.status_code == 401

    def test_post_with_wrong_token_returns_401(self, lan_client: TestClient) -> None:
        response = lan_client.post("/test/mutate", headers={"Authorization": "Bearer wrong"})
        assert response.status_code == 401

    def test_post_with_correct_token_succeeds(self, lan_client: TestClient) -> None:
        response = lan_client.post("/test/mutate", headers={"Authorization": "Bearer test-token"})
        assert response.status_code == 200

    def test_delete_without_token_returns_401(self, lan_client: TestClient) -> None:
        response = lan_client.delete("/test/delete")
        assert response.status_code == 401

    def test_get_no_auth_required(self, lan_client: TestClient) -> None:
        """Read-only endpoints never require auth, even in LAN mode."""
        response = lan_client.get("/test/read")
        assert response.status_code == 200

    def test_401_response_has_envelope_format(self, lan_client: TestClient) -> None:
        """FR-039: 401 auth rejection uses the standard error envelope."""
        response = lan_client.post("/test/mutate")
        body = response.json()
        assert body["ok"] is False
        assert body["error"]["code"] == "UNAUTHORIZED"
        assert isinstance(body["error"]["message"], str)
        assert len(body["error"]["message"]) > 0


class TestMisconfiguredLanMode:
    """FR-039, FR-044: Misconfigured LAN mode (no auth token) returns envelope-shaped 503."""

    def test_503_no_auth_token_has_envelope_format(self) -> None:
        settings = Settings(
            mode="lan",
            auth_token=None,
            allowed_origins=["http://localhost"],
        )
        client = TestClient(_make_app(settings), raise_server_exceptions=False)
        response = client.post("/test/mutate")
        assert response.status_code == 503
        body = response.json()
        assert body["ok"] is False
        assert body["error"]["code"] == "AUTH_MISCONFIGURED"
        assert isinstance(body["error"]["message"], str)
