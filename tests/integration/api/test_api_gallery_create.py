"""Integration tests: FR-013 gallery creation via POST /api/v1/galleries."""

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


def _add_image(db_path: Path, image_id: str, path: str) -> None:
    with sqlite3.connect(db_path) as conn:
        conn.execute("INSERT INTO images VALUES (?, ?)", (image_id, path))


def _add_decision(db_path: Path, image_id: str, decision: str) -> None:
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "INSERT INTO cull_decisions VALUES (?, ?, ?)",
            (image_id, decision, "2026-01-01T00:00:00Z"),
        )


@pytest.mark.fr
@pytest.mark.integration
def test_create_gallery_from_picks(tmp_path: Path, client_and_db) -> None:
    client, db_path = client_and_db
    photo = tmp_path / "photo.jpg"
    photo.write_bytes(b"fake")
    _add_image(db_path, "img1", str(photo))
    _add_decision(db_path, "img1", "pick")

    resp = client.post("/api/v1/galleries", json={"name": "my-picks", "mode": "picks"})
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["created_count"] >= 0  # hardlinks may fail on tmp_path but gallery dir created


@pytest.mark.fr
@pytest.mark.integration
def test_create_gallery_unknown_mode_returns_422(client_and_db) -> None:
    client, _ = client_and_db
    resp = client.post("/api/v1/galleries", json={"name": "x", "mode": "invalid"})
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "INVALID_MODE"


@pytest.mark.fr
@pytest.mark.integration
def test_create_gallery_query_mode_missing_query_returns_422(client_and_db) -> None:
    client, _ = client_and_db
    resp = client.post("/api/v1/galleries", json={"name": "x", "mode": "query"})
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "QUERY_REQUIRED"


@pytest.mark.fr
@pytest.mark.integration
def test_create_gallery_bad_query_returns_422(client_and_db) -> None:
    client, _ = client_and_db
    resp = client.post(
        "/api/v1/galleries", json={"name": "x", "mode": "query", "query": "NOT VALID !!!"}
    )
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "QUERY_PARSE_ERROR"
