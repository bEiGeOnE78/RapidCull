"""Integration tests for /api/v1/galleries endpoints.

Uses FastAPI TestClient with a temporary SQLite database per test.
The galleries router is configured via configure_router() and mounted on a
local FastAPI app to isolate from the global app instance.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from rapidcull.api_envelope import register_handlers
from rapidcull.api_galleries import configure_router, router
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
def client(db_path: Path) -> TestClient:
    """TestClient for an app with the galleries router mounted."""
    configure_router(db_path)
    app = FastAPI()
    register_handlers(app)
    app.include_router(router)
    return TestClient(app, raise_server_exceptions=False)


def _insert_image(db_path: Path, image_id: str, path: str) -> None:
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "INSERT INTO images (image_id, path) VALUES (?, ?)",
            (image_id, path),
        )


def _insert_decision(db_path: Path, image_id: str, decision: str) -> None:
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "INSERT INTO cull_decisions (image_id, decision, decided_at)"
            " VALUES (?, ?, datetime('now'))",
            (image_id, decision),
        )


# ---------------------------------------------------------------------------
# GET /api/v1/galleries
# ---------------------------------------------------------------------------


class TestListGalleries:
    def test_list_galleries_empty(self, client: TestClient) -> None:
        """No images in DB → empty galleries list."""
        resp = client.get("/api/v1/galleries")
        assert resp.status_code == 200
        body = resp.json()
        assert body["ok"] is True
        assert body["data"]["galleries"] == []

    def test_list_galleries_groups_by_directory(self, db_path: Path, client: TestClient) -> None:
        """3 images in 2 directories → 2 galleries with correct image counts."""
        _insert_image(db_path, "img_001", "/photos/2024/a.jpg")
        _insert_image(db_path, "img_002", "/photos/2024/b.jpg")
        _insert_image(db_path, "img_003", "/photos/2023/c.jpg")

        resp = client.get("/api/v1/galleries")
        assert resp.status_code == 200
        body = resp.json()
        assert body["ok"] is True
        galleries = body["data"]["galleries"]
        assert len(galleries) == 2

        # Sort by path for deterministic assertion
        by_path = {g["path"]: g for g in galleries}
        assert by_path["/photos/2023"]["image_count"] == 1
        assert by_path["/photos/2024"]["image_count"] == 2

    def test_list_galleries_single_directory(self, db_path: Path, client: TestClient) -> None:
        """Single directory → one gallery with correct count."""
        _insert_image(db_path, "img_001", "/shots/a.jpg")
        _insert_image(db_path, "img_002", "/shots/b.jpg")

        resp = client.get("/api/v1/galleries")
        assert resp.status_code == 200
        galleries = resp.json()["data"]["galleries"]
        assert len(galleries) == 1
        assert galleries[0]["image_count"] == 2
        assert galleries[0]["path"] == "/shots"


# ---------------------------------------------------------------------------
# GET /api/v1/galleries/{gallery_id}/images
# ---------------------------------------------------------------------------


def _get_gallery_id(client: TestClient) -> str:
    """Helper: list galleries and return the first gallery_id."""
    resp = client.get("/api/v1/galleries")
    return str(resp.json()["data"]["galleries"][0]["gallery_id"])


class TestGetGalleryImages:
    def test_get_gallery_images_not_found(self, client: TestClient) -> None:
        """Unknown gallery_id → 404."""
        # Use a valid base64 encoding of a non-existent path
        import base64

        fake_id = base64.urlsafe_b64encode(b"/nonexistent/path").decode()
        resp = client.get(f"/api/v1/galleries/{fake_id}/images")
        assert resp.status_code == 404
        body = resp.json()
        assert body["ok"] is False
        assert body["error"]["code"] == "GALLERY_NOT_FOUND"

    def test_get_gallery_images_returns_images(self, db_path: Path, client: TestClient) -> None:
        """Insert images → GET gallery images → returns image list."""
        _insert_image(db_path, "img_001", "/photos/a.jpg")
        _insert_image(db_path, "img_002", "/photos/b.jpg")

        gallery_id = _get_gallery_id(client)
        resp = client.get(f"/api/v1/galleries/{gallery_id}/images")
        assert resp.status_code == 200
        body = resp.json()
        assert body["ok"] is True
        data = body["data"]
        assert data["total"] == 2
        assert len(data["images"]) == 2

        image_ids = {img["image_id"] for img in data["images"]}
        assert image_ids == {"img_001", "img_002"}

        for img in data["images"]:
            assert "image_id" in img
            assert "path" in img
            assert "thumbnail_path" in img
            assert "decision" in img

    def test_get_gallery_images_decision_reflected(self, db_path: Path, client: TestClient) -> None:
        """Image with pick decision → decision field is 'pick'."""
        _insert_image(db_path, "img_001", "/photos/a.jpg")
        _insert_decision(db_path, "img_001", "pick")

        gallery_id = _get_gallery_id(client)
        resp = client.get(f"/api/v1/galleries/{gallery_id}/images")
        assert resp.status_code == 200
        images = resp.json()["data"]["images"]
        assert len(images) == 1
        assert images[0]["decision"] == "pick"

    def test_get_gallery_images_no_decision_is_null(
        self, db_path: Path, client: TestClient
    ) -> None:
        """Image with no decision → decision field is null."""
        _insert_image(db_path, "img_001", "/photos/a.jpg")

        gallery_id = _get_gallery_id(client)
        resp = client.get(f"/api/v1/galleries/{gallery_id}/images")
        assert resp.status_code == 200
        images = resp.json()["data"]["images"]
        assert images[0]["decision"] is None

    def test_get_gallery_images_pagination(self, db_path: Path, client: TestClient) -> None:
        """Insert 10 images → page_size=3 → 3 results returned, total=10."""
        for i in range(10):
            _insert_image(db_path, f"img_{i:03d}", f"/photos/img_{i:03d}.jpg")

        gallery_id = _get_gallery_id(client)
        resp = client.get(f"/api/v1/galleries/{gallery_id}/images?page=1&page_size=3")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["total"] == 10
        assert data["page"] == 1
        assert data["page_size"] == 3
        assert len(data["images"]) == 3

    def test_get_gallery_images_pagination_page2(self, db_path: Path, client: TestClient) -> None:
        """Second page of results returns next 3 images."""
        for i in range(10):
            _insert_image(db_path, f"img_{i:03d}", f"/photos/img_{i:03d}.jpg")

        gallery_id = _get_gallery_id(client)
        resp = client.get(f"/api/v1/galleries/{gallery_id}/images?page=2&page_size=3")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["total"] == 10
        assert data["page"] == 2
        assert len(data["images"]) == 3
