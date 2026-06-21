"""Integration tests: user gallery CRUD via /api/v1/galleries endpoints.

Covers: create, list, add images, get images, remove image, delete gallery,
and rejection of mutations on source-dir and virtual galleries.
"""

from __future__ import annotations

import base64
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
    path = tmp_path / "test.db"
    create_or_validate_schema(path)
    return path


@pytest.fixture()
def client(db_path: Path) -> TestClient:
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


def _source_gallery_id(dir_path: str) -> str:
    """Encode a directory path to URL-safe base64, matching api_galleries logic."""
    return base64.urlsafe_b64encode(dir_path.encode()).decode()


def _create_gallery(client: TestClient, name: str) -> str:
    """Helper: create a user gallery and return its gallery_id."""
    resp = client.post("/api/v1/galleries", json={"name": name})
    assert resp.status_code == 201
    return str(resp.json()["data"]["gallery_id"])


# ---------------------------------------------------------------------------
# POST /api/v1/galleries — create manual user gallery
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_create_user_gallery_returns_201(client: TestClient, db_path: Path) -> None:
    """POST {name} → 201 with type='user', source='manual', count=0."""
    resp = client.post("/api/v1/galleries", json={"name": "My Gallery"})
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["type"] == "user"
    assert data["source"] == "manual"
    assert data["name"] == "My Gallery"
    assert data["count"] == 0
    assert "gallery_id" in data

    # Verify DB row
    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            "SELECT name, source FROM galleries WHERE gallery_id = ?",
            (data["gallery_id"],),
        ).fetchone()
    assert row == ("My Gallery", "manual")


@pytest.mark.integration
def test_create_gallery_missing_name_returns_422(client: TestClient) -> None:
    """POST with empty body → 422."""
    resp = client.post("/api/v1/galleries", json={})
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# GET /api/v1/galleries — list includes new user gallery and virtuals
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_list_includes_user_gallery_and_virtuals(client: TestClient, db_path: Path) -> None:
    """After creation, GET /api/v1/galleries includes the new gallery plus all 3 virtuals."""
    _insert_image(db_path, "img_001", "/photos/a.jpg")
    gallery_id = _create_gallery(client, "My Gallery")

    resp = client.get("/api/v1/galleries")
    assert resp.status_code == 200
    galleries = resp.json()["data"]["galleries"]

    types = {g["type"] for g in galleries}
    assert "user" in types
    assert "source" in types
    assert "virtual" in types

    user_ids = {g["gallery_id"] for g in galleries if g["type"] == "user"}
    assert gallery_id in user_ids

    virtual_ids = {g["gallery_id"] for g in galleries if g["type"] == "virtual"}
    assert virtual_ids == {"virtual:picks", "virtual:rejects", "virtual:trash"}


# ---------------------------------------------------------------------------
# POST /api/v1/galleries/{id}/images — add images to user gallery
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_add_images_to_gallery_increases_count(client: TestClient, db_path: Path) -> None:
    """POST image_ids to gallery → membership rows created, count in list goes up."""
    _insert_image(db_path, "img_001", "/photos/a.jpg")
    _insert_image(db_path, "img_002", "/photos/b.jpg")
    _insert_image(db_path, "img_003", "/photos/c.jpg")
    gallery_id = _create_gallery(client, "Test Gallery")

    resp = client.post(
        f"/api/v1/galleries/{gallery_id}/images",
        json={"image_ids": ["img_001", "img_002"]},
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["added_count"] == 2

    # Check count in list
    list_resp = client.get("/api/v1/galleries")
    user_gallery = next(
        g for g in list_resp.json()["data"]["galleries"] if g["gallery_id"] == gallery_id
    )
    assert user_gallery["count"] == 2


@pytest.mark.integration
def test_add_images_to_virtual_gallery_returns_400(client: TestClient) -> None:
    """POST images to virtual gallery → 400 GALLERY_NOT_MUTABLE."""
    resp = client.post(
        "/api/v1/galleries/virtual:picks/images",
        json={"image_ids": ["img_001"]},
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "GALLERY_NOT_MUTABLE"


@pytest.mark.integration
def test_add_images_to_source_gallery_returns_404(client: TestClient, db_path: Path) -> None:
    """POST images to source-dir gallery → 404 (not a user gallery)."""
    _insert_image(db_path, "img_001", "/photos/a.jpg")
    source_id = _source_gallery_id("/photos")

    resp = client.post(
        f"/api/v1/galleries/{source_id}/images",
        json={"image_ids": ["img_001"]},
    )
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# GET /api/v1/galleries/{id}/images — images in user gallery
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_get_user_gallery_images_returns_added_images(client: TestClient, db_path: Path) -> None:
    """GET images after add → returns the added image_ids."""
    _insert_image(db_path, "img_001", "/photos/a.jpg")
    _insert_image(db_path, "img_002", "/photos/b.jpg")
    gallery_id = _create_gallery(client, "Gallery A")

    client.post(
        f"/api/v1/galleries/{gallery_id}/images",
        json={"image_ids": ["img_001", "img_002"]},
    )

    resp = client.get(f"/api/v1/galleries/{gallery_id}/images")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["total"] == 2
    ids = {img["image_id"] for img in data["images"]}
    assert ids == {"img_001", "img_002"}


# ---------------------------------------------------------------------------
# DELETE /api/v1/galleries/{id}/images/{image_id} — remove from user gallery
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_remove_image_from_user_gallery(client: TestClient, db_path: Path) -> None:
    """DELETE image from user gallery → membership row removed, count decreases."""
    _insert_image(db_path, "img_001", "/photos/a.jpg")
    _insert_image(db_path, "img_002", "/photos/b.jpg")
    gallery_id = _create_gallery(client, "Removable")

    client.post(
        f"/api/v1/galleries/{gallery_id}/images",
        json={"image_ids": ["img_001", "img_002"]},
    )

    resp = client.delete(f"/api/v1/galleries/{gallery_id}/images/img_001")
    assert resp.status_code == 200
    assert resp.json()["data"]["removed_count"] == 1

    # Verify only img_002 remains
    images_resp = client.get(f"/api/v1/galleries/{gallery_id}/images")
    ids = {img["image_id"] for img in images_resp.json()["data"]["images"]}
    assert ids == {"img_002"}


@pytest.mark.integration
def test_remove_image_from_source_gallery_returns_4xx(client: TestClient, db_path: Path) -> None:
    """DELETE image from source-dir gallery → 4xx (not allowed)."""
    _insert_image(db_path, "img_001", "/photos/a.jpg")
    source_id = _source_gallery_id("/photos")

    resp = client.delete(f"/api/v1/galleries/{source_id}/images/img_001")
    assert resp.status_code in (400, 404)


@pytest.mark.integration
def test_remove_image_from_virtual_gallery_returns_400(client: TestClient) -> None:
    """DELETE image from virtual gallery → 400 GALLERY_NOT_MUTABLE."""
    resp = client.delete("/api/v1/galleries/virtual:picks/images/img_001")
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "GALLERY_NOT_MUTABLE"


# ---------------------------------------------------------------------------
# DELETE /api/v1/galleries/{id} — delete user gallery
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_delete_user_gallery_removes_row_and_memberships(client: TestClient, db_path: Path) -> None:
    """DELETE user gallery → row and memberships cascade-deleted."""
    _insert_image(db_path, "img_001", "/photos/a.jpg")
    gallery_id = _create_gallery(client, "Deletable")

    client.post(
        f"/api/v1/galleries/{gallery_id}/images",
        json={"image_ids": ["img_001"]},
    )

    resp = client.delete(f"/api/v1/galleries/{gallery_id}")
    assert resp.status_code == 200
    assert resp.json()["data"]["deleted"] is True

    # Verify gallery row gone
    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            "SELECT gallery_id FROM galleries WHERE gallery_id = ?", (gallery_id,)
        ).fetchone()
        membership = conn.execute(
            "SELECT gallery_id FROM gallery_memberships WHERE gallery_id = ?", (gallery_id,)
        ).fetchone()
    assert row is None
    assert membership is None

    # No longer appears in list
    list_resp = client.get("/api/v1/galleries")
    user_ids = {
        g["gallery_id"] for g in list_resp.json()["data"]["galleries"] if g["type"] == "user"
    }
    assert gallery_id not in user_ids


@pytest.mark.integration
def test_delete_source_gallery_returns_404(client: TestClient, db_path: Path) -> None:
    """DELETE source-dir gallery → 404 (source galleries are not deletable)."""
    _insert_image(db_path, "img_001", "/photos/a.jpg")
    source_id = _source_gallery_id("/photos")

    resp = client.delete(f"/api/v1/galleries/{source_id}")
    assert resp.status_code == 404


@pytest.mark.integration
def test_delete_virtual_gallery_returns_400(client: TestClient) -> None:
    """DELETE virtual gallery → 400 GALLERY_NOT_MUTABLE."""
    resp = client.delete("/api/v1/galleries/virtual:picks")
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "GALLERY_NOT_MUTABLE"
