"""Integration tests: GET /api/v1/images/{image_id}/galleries endpoint.

Covers:
- Returns source-dir gallery for any ingested image
- Returns both source-dir and user gallery after membership is added
- Returns 404 for unknown image_id
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from rapidcull.api_envelope import register_handlers
from rapidcull.api_galleries import configure_router as configure_galleries_router
from rapidcull.api_galleries import router as galleries_router
from rapidcull.api_images import configure_router as configure_images_router
from rapidcull.api_images import router as images_router
from rapidcull.schema import create_or_validate_schema

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def db_path(tmp_path: Path) -> Path:
    path = tmp_path / "test.db"
    create_or_validate_schema(path)
    return path


@pytest.fixture()
def client(db_path: Path) -> TestClient:
    configure_galleries_router(db_path)
    configure_images_router(db_path)
    app = FastAPI()
    register_handlers(app)
    app.include_router(galleries_router)
    app.include_router(images_router)
    return TestClient(app, raise_server_exceptions=False)


def _insert_image(db_path: Path, image_id: str, path: str) -> None:
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "INSERT INTO images (image_id, path) VALUES (?, ?)",
            (image_id, path),
        )


def _create_gallery(client: TestClient, name: str) -> str:
    resp = client.post("/api/v1/galleries", json={"name": name})
    assert resp.status_code == 201
    return str(resp.json()["data"]["gallery_id"])


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_get_image_galleries_returns_source_dir(client: TestClient, db_path: Path) -> None:
    """GET /images/{id}/galleries for an ingested image returns at least the source-dir gallery."""
    _insert_image(db_path, "img_001", "/photos/a.jpg")

    resp = client.get("/api/v1/images/img_001/galleries")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["image_id"] == "img_001"
    galleries = data["galleries"]
    assert len(galleries) >= 1

    source_galleries = [g for g in galleries if g["type"] == "source"]
    assert len(source_galleries) == 1
    assert "gallery_id" in source_galleries[0]
    assert "name" in source_galleries[0]


@pytest.mark.integration
def test_get_image_galleries_includes_user_gallery_after_add(
    client: TestClient, db_path: Path
) -> None:
    """After adding image to a user gallery, GET /images/{id}/galleries returns both."""
    _insert_image(db_path, "img_001", "/photos/a.jpg")
    gallery_id = _create_gallery(client, "My Gallery")

    client.post(
        f"/api/v1/galleries/{gallery_id}/images",
        json={"image_ids": ["img_001"]},
    )

    resp = client.get("/api/v1/images/img_001/galleries")
    assert resp.status_code == 200
    galleries = resp.json()["data"]["galleries"]

    types = {g["type"] for g in galleries}
    assert "source" in types
    assert "user" in types

    user_gallery = next(g for g in galleries if g["type"] == "user")
    assert user_gallery["gallery_id"] == gallery_id
    assert user_gallery["name"] == "My Gallery"


@pytest.mark.integration
def test_get_image_galleries_unknown_image_returns_404(client: TestClient) -> None:
    """GET /images/nonexistent/galleries → 404 IMAGE_NOT_FOUND."""
    resp = client.get("/api/v1/images/no-such-image/galleries")
    assert resp.status_code == 404
    body = resp.json()
    assert body["ok"] is False
    assert body["error"]["code"] == "IMAGE_NOT_FOUND"


@pytest.mark.integration
def test_get_image_galleries_after_removal_user_gallery_gone(
    client: TestClient, db_path: Path
) -> None:
    """After removing image from user gallery, it no longer appears in gallery list."""
    _insert_image(db_path, "img_001", "/photos/a.jpg")
    gallery_id = _create_gallery(client, "Removable")

    client.post(
        f"/api/v1/galleries/{gallery_id}/images",
        json={"image_ids": ["img_001"]},
    )

    # Verify it's there
    before = client.get("/api/v1/images/img_001/galleries").json()["data"]["galleries"]
    assert any(g["gallery_id"] == gallery_id for g in before)

    # Remove
    client.delete(f"/api/v1/galleries/{gallery_id}/images/img_001")

    after = client.get("/api/v1/images/img_001/galleries").json()["data"]["galleries"]
    assert not any(g["gallery_id"] == gallery_id for g in after)
    # Source-dir gallery is still there
    assert any(g["type"] == "source" for g in after)
