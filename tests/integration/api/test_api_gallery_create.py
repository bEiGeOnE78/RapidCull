"""Integration tests: FR-013 gallery creation via POST /api/v1/galleries.

New shape (wave 1-2 refactor): POST body is {name: string}, creates a manual
user gallery stored in the `galleries` DB table. Old mode-based approach is gone.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from rapidcull.api import create_app
from rapidcull.jobs import get_job_store
from rapidcull.schema import create_or_validate_schema


@pytest.fixture(autouse=True)
def _clear_jobs() -> None:
    get_job_store().clear()


@pytest.fixture()
def client_and_db(tmp_path: Path):
    db_path = tmp_path / "test.db"
    create_or_validate_schema(db_path)
    client = TestClient(create_app(db_path=db_path))
    return client, db_path


@pytest.mark.fr
@pytest.mark.integration
def test_create_gallery_creates_db_row(tmp_path: Path, client_and_db) -> None:
    """POST /api/v1/galleries with {name} → 201, row in galleries table."""
    client, db_path = client_and_db

    resp = client.post("/api/v1/galleries", json={"name": "my-picks"})
    assert resp.status_code == 201

    data = resp.json()["data"]
    assert data["name"] == "my-picks"
    assert data["type"] == "user"
    assert data["source"] == "manual"
    assert "gallery_id" in data

    # Verify row exists in DB
    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            "SELECT name, source FROM galleries WHERE gallery_id = ?",
            (data["gallery_id"],),
        ).fetchone()
    assert row is not None
    assert row[0] == "my-picks"
    assert row[1] == "manual"


@pytest.mark.fr
@pytest.mark.integration
def test_create_gallery_returns_gallery_shape(client_and_db) -> None:
    """Response contains all required Gallery fields."""
    client, _ = client_and_db

    resp = client.post("/api/v1/galleries", json={"name": "test-gallery"})
    assert resp.status_code == 201

    data = resp.json()["data"]
    assert "gallery_id" in data
    assert "name" in data
    assert "type" in data
    assert "source" in data
    assert "count" in data
    assert data["count"] == 0  # empty on creation


@pytest.mark.fr
@pytest.mark.integration
def test_create_gallery_appears_in_list(client_and_db) -> None:
    """Newly created gallery appears in GET /api/v1/galleries as type='user'."""
    client, _ = client_and_db

    create_resp = client.post("/api/v1/galleries", json={"name": "visible-gallery"})
    gallery_id = create_resp.json()["data"]["gallery_id"]

    list_resp = client.get("/api/v1/galleries")
    assert list_resp.status_code == 200
    galleries = list_resp.json()["data"]["galleries"]
    user_galleries = [g for g in galleries if g["type"] == "user"]
    ids = {g["gallery_id"] for g in user_galleries}
    assert gallery_id in ids


@pytest.mark.fr
@pytest.mark.integration
def test_create_gallery_missing_name_returns_422(client_and_db) -> None:
    """POST with empty body → 422 validation error."""
    client, _ = client_and_db
    resp = client.post("/api/v1/galleries", json={})
    assert resp.status_code == 422
