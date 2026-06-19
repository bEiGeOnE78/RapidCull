"""Integration tests for /api/v1/trash endpoints.

Uses FastAPI TestClient with a temporary SQLite database per test session.
The trash router is configured via configure_router() and mounted on a local
FastAPI app to isolate from the global app instance.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from rapidcull.api_envelope import register_handlers
from rapidcull.api_trash import configure_router, router
from rapidcull.culling import move_to_trash, set_decision
from rapidcull.schema import create_or_validate_schema

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _add_image(db_path: Path, image_id: str, path: str) -> None:
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "INSERT INTO images (image_id, path) VALUES (?, ?)",
            (image_id, path),
        )


def _make_file(path: Path, content: bytes = b"pixels") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


def _trash_item(db_path: Path, trash_dir: Path, tmp_path: Path, image_id: str) -> None:
    """Add an image, reject it, and move it to trash."""
    photo = tmp_path / "photos" / f"{image_id}.jpg"
    _make_file(photo)
    _add_image(db_path, image_id, str(photo))
    set_decision(db_path, image_id, "reject")
    move_to_trash(db_path, [image_id], trash_dir)


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
def trash_dir(db_path: Path) -> Path:
    """Return the trash directory derived from db_path (mirrors api_trash logic)."""
    return db_path.parent / ".trash"


@pytest.fixture()
def client(db_path: Path) -> TestClient:
    """TestClient for an app with the trash router mounted."""
    configure_router(db_path)
    app = FastAPI()
    register_handlers(app)
    app.include_router(router)
    return TestClient(app, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# GET /api/v1/trash
# ---------------------------------------------------------------------------


class TestListTrash:
    def test_list_trash_empty(self, client: TestClient) -> None:
        resp = client.get("/api/v1/trash")
        assert resp.status_code == 200
        body = resp.json()
        assert body["ok"] is True
        assert body["data"]["items"] == []
        assert body["data"]["count"] == 0

    def test_list_trash_returns_items(
        self, db_path: Path, trash_dir: Path, tmp_path: Path, client: TestClient
    ) -> None:
        _trash_item(db_path, trash_dir, tmp_path, "img_001")

        resp = client.get("/api/v1/trash")
        assert resp.status_code == 200
        body = resp.json()
        assert body["ok"] is True
        data = body["data"]
        assert data["count"] == 1
        item = data["items"][0]
        assert item["image_id"] == "img_001"
        assert "original_path" in item
        assert item["original_path"] != ""
        assert "trashed_at" in item


# ---------------------------------------------------------------------------
# POST /api/v1/trash/{image_id}/restore
# ---------------------------------------------------------------------------


class TestRestoreFromTrash:
    def test_restore_not_in_trash(self, client: TestClient) -> None:
        resp = client.post("/api/v1/trash/img_missing/restore")
        assert resp.status_code == 404
        body = resp.json()
        assert body["ok"] is False
        assert body["error"]["code"] == "TRASH_RESTORE_FAILED"

    def test_restore_removes_from_trash(
        self, db_path: Path, trash_dir: Path, tmp_path: Path, client: TestClient
    ) -> None:
        _trash_item(db_path, trash_dir, tmp_path, "img_002")

        resp = client.post("/api/v1/trash/img_002/restore")
        assert resp.status_code == 200
        assert resp.json()["ok"] is True

        # Item should no longer be in trash
        list_resp = client.get("/api/v1/trash")
        items = list_resp.json()["data"]["items"]
        assert not any(i["image_id"] == "img_002" for i in items)

    def test_restore_adds_back_to_images(
        self, db_path: Path, trash_dir: Path, tmp_path: Path, client: TestClient
    ) -> None:
        _trash_item(db_path, trash_dir, tmp_path, "img_003")

        resp = client.post("/api/v1/trash/img_003/restore")
        assert resp.status_code == 200
        assert resp.json()["data"]["image_id"] == "img_003"

        # Item should be back in images table
        with sqlite3.connect(db_path) as conn:
            row = conn.execute(
                "SELECT image_id FROM images WHERE image_id = ?", ("img_003",)
            ).fetchone()
        assert row is not None
        assert row[0] == "img_003"
