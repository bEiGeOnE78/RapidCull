"""Integration tests for /api/v1/images endpoints (FR-025, FR-026, FR-028).

Uses FastAPI TestClient with a temporary SQLite database per test session.
The images router is configured via configure_router() and mounted on a local
FastAPI app to isolate from the global app instance.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from rapidcull.api_envelope import register_handlers
from rapidcull.api_images import configure_router, router
from rapidcull.schema import create_or_validate_schema

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def db_path(tmp_path: Path) -> Path:
    """Create a fresh SQLite database with the full schema."""
    path = tmp_path / "test.db"
    create_or_validate_schema(path)
    return path


@pytest.fixture()
def seeded_db(db_path: Path) -> tuple[Path, str]:
    """Insert a single image row and return (db_path, image_id)."""
    image_id = "img_001"
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "INSERT INTO images (image_id, path) VALUES (?, ?)",
            (image_id, "/photos/img_001.jpg"),
        )
    return db_path, image_id


@pytest.fixture()
def client(db_path: Path) -> TestClient:
    """TestClient for an app with the images router mounted."""
    configure_router(db_path)
    app = FastAPI()
    register_handlers(app)
    app.include_router(router)
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture()
def seeded_client(seeded_db: tuple[Path, str]) -> tuple[TestClient, str]:
    """TestClient plus the seeded image_id."""
    path, image_id = seeded_db
    configure_router(path)
    app = FastAPI()
    register_handlers(app)
    app.include_router(router)
    return TestClient(app, raise_server_exceptions=False), image_id


# ---------------------------------------------------------------------------
# GET /api/v1/images/{image_id}
# ---------------------------------------------------------------------------


class TestGetImage:
    def test_unknown_image_returns_404(self, client: TestClient) -> None:
        resp = client.get("/api/v1/images/img_missing")
        assert resp.status_code == 404
        body = resp.json()
        assert body["ok"] is False
        assert body["error"]["code"] == "IMAGE_NOT_FOUND"

    def test_known_image_returns_200_with_fields(
        self, seeded_client: tuple[TestClient, str]
    ) -> None:
        client, image_id = seeded_client
        resp = client.get(f"/api/v1/images/{image_id}")
        assert resp.status_code == 200
        body = resp.json()
        assert body["ok"] is True
        data = body["data"]
        assert data["image_id"] == image_id
        assert data["path"] == "/photos/img_001.jpg"
        assert "face_count" in data
        assert isinstance(data["face_count"], int)
        assert "decision" in data

    def test_image_with_no_decision_has_null_decision(
        self, seeded_client: tuple[TestClient, str]
    ) -> None:
        client, image_id = seeded_client
        resp = client.get(f"/api/v1/images/{image_id}")
        assert resp.json()["data"]["decision"] is None

    def test_image_face_count_is_zero_with_no_faces(
        self, seeded_client: tuple[TestClient, str]
    ) -> None:
        client, image_id = seeded_client
        resp = client.get(f"/api/v1/images/{image_id}")
        assert resp.json()["data"]["face_count"] == 0


# ---------------------------------------------------------------------------
# GET /api/v1/images/{image_id}/decision
# ---------------------------------------------------------------------------


class TestGetDecision:
    def test_no_decision_returns_null_data(self, seeded_client: tuple[TestClient, str]) -> None:
        client, image_id = seeded_client
        resp = client.get(f"/api/v1/images/{image_id}/decision")
        assert resp.status_code == 200
        body = resp.json()
        assert body["ok"] is True
        assert body["data"] is None

    def test_decision_after_pick_returns_pick(self, seeded_client: tuple[TestClient, str]) -> None:
        client, image_id = seeded_client
        client.post(f"/api/v1/images/{image_id}/decision", json={"decision": "pick"})

        resp = client.get(f"/api/v1/images/{image_id}/decision")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["image_id"] == image_id
        assert data["decision"] == "pick"
        assert "decided_at" in data

    def test_unknown_image_returns_404(self, client: TestClient) -> None:
        resp = client.get("/api/v1/images/img_missing/decision")
        assert resp.status_code == 404
        body = resp.json()
        assert body["ok"] is False
        assert body["error"]["code"] == "IMAGE_NOT_FOUND"


# ---------------------------------------------------------------------------
# POST /api/v1/images/{image_id}/decision
# ---------------------------------------------------------------------------


class TestPostDecision:
    def test_pick_returns_200_ok(self, seeded_client: tuple[TestClient, str]) -> None:
        client, image_id = seeded_client
        resp = client.post(f"/api/v1/images/{image_id}/decision", json={"decision": "pick"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["ok"] is True
        assert body["data"]["image_id"] == image_id
        assert body["data"]["success"] is True

    def test_reject_returns_200_ok(self, seeded_client: tuple[TestClient, str]) -> None:
        client, image_id = seeded_client
        resp = client.post(f"/api/v1/images/{image_id}/decision", json={"decision": "reject"})
        assert resp.status_code == 200
        assert resp.json()["ok"] is True

    def test_invalid_decision_value_returns_422(
        self, seeded_client: tuple[TestClient, str]
    ) -> None:
        client, image_id = seeded_client
        resp = client.post(f"/api/v1/images/{image_id}/decision", json={"decision": "maybe"})
        assert resp.status_code == 422
        body = resp.json()
        assert body["ok"] is False
        assert body["error"]["code"] == "VALIDATION_ERROR"

    def test_nonexistent_image_returns_404(self, client: TestClient) -> None:
        resp = client.post("/api/v1/images/img_missing/decision", json={"decision": "pick"})
        assert resp.status_code == 404
        body = resp.json()
        assert body["ok"] is False
        assert body["error"]["code"] == "IMAGE_NOT_FOUND"


# ---------------------------------------------------------------------------
# DELETE /api/v1/images/{image_id}/decision
# ---------------------------------------------------------------------------


class TestDeleteDecision:
    def test_delete_decision_returns_200(self, seeded_client: tuple[TestClient, str]) -> None:
        client, image_id = seeded_client
        client.post(f"/api/v1/images/{image_id}/decision", json={"decision": "pick"})

        resp = client.delete(f"/api/v1/images/{image_id}/decision")
        assert resp.status_code == 200
        body = resp.json()
        assert body["ok"] is True
        assert body["data"]["image_id"] == image_id
        assert body["data"]["success"] is True

    def test_get_decision_after_delete_is_null(self, seeded_client: tuple[TestClient, str]) -> None:
        client, image_id = seeded_client
        client.post(f"/api/v1/images/{image_id}/decision", json={"decision": "reject"})
        client.delete(f"/api/v1/images/{image_id}/decision")

        resp = client.get(f"/api/v1/images/{image_id}/decision")
        assert resp.json()["data"] is None
