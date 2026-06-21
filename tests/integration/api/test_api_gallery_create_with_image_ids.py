"""Integration tests: POST /api/v1/galleries with optional image_ids.

Verifies that gallery creation accepts an image_ids list and
creates gallery_memberships rows for each provided image.
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from rapidcull.api import create_app
from rapidcull.jobs import get_job_store
from rapidcull.schema import create_or_validate_schema


@pytest.fixture(autouse=True)
def _clear_jobs() -> None:
    get_job_store().clear()


def _insert_image(conn: sqlite3.Connection, path: str) -> str:
    image_id = uuid.uuid4().hex
    conn.execute(
        "INSERT INTO images (image_id, path, metadata) VALUES (?, ?, ?)",
        (image_id, path, json.dumps({})),
    )
    return image_id


@pytest.fixture()
def client_and_db(tmp_path: Path):
    db_path = tmp_path / "test.db"
    create_or_validate_schema(db_path)
    with sqlite3.connect(db_path) as conn:
        img1 = _insert_image(conn, "/photos/a.jpg")
        img2 = _insert_image(conn, "/photos/b.jpg")
        img3 = _insert_image(conn, "/photos/c.jpg")
        conn.commit()
    client = TestClient(create_app(db_path=db_path))
    return client, db_path, [img1, img2, img3]


@pytest.mark.fr
@pytest.mark.integration
def test_create_gallery_with_image_ids_creates_memberships(client_and_db) -> None:
    """POST /api/v1/galleries with image_ids → gallery row + membership rows."""
    client, db_path, (img1, img2, img3) = client_and_db

    resp = client.post(
        "/api/v1/galleries",
        json={"name": "search-results", "image_ids": [img1, img2]},
    )
    assert resp.status_code == 201
    data = resp.json()["data"]
    gallery_id = data["gallery_id"]
    assert data["name"] == "search-results"
    assert data["count"] == 2

    # Verify memberships in DB
    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            "SELECT image_id FROM gallery_memberships WHERE gallery_id = ? ORDER BY image_id",
            (gallery_id,),
        ).fetchall()
    member_ids = {row[0] for row in rows}
    assert img1 in member_ids
    assert img2 in member_ids
    assert img3 not in member_ids


@pytest.mark.fr
@pytest.mark.integration
def test_create_gallery_without_image_ids_still_works(client_and_db) -> None:
    """POST /api/v1/galleries without image_ids → empty gallery (backward compat)."""
    client, db_path, _ = client_and_db

    resp = client.post("/api/v1/galleries", json={"name": "empty-gallery"})
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["count"] == 0

    with sqlite3.connect(db_path) as conn:
        count = conn.execute(
            "SELECT COUNT(*) FROM gallery_memberships WHERE gallery_id = ?",
            (data["gallery_id"],),
        ).fetchone()[0]
    assert count == 0


@pytest.mark.fr
@pytest.mark.integration
def test_create_gallery_with_empty_image_ids_list(client_and_db) -> None:
    """POST /api/v1/galleries with image_ids=[] → empty gallery."""
    client, db_path, _ = client_and_db

    resp = client.post("/api/v1/galleries", json={"name": "explicit-empty", "image_ids": []})
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["count"] == 0
