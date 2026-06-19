"""Integration tests for /api/v1/persons endpoints.

Uses FastAPI TestClient with a temporary SQLite database per test session.
The persons router is configured via configure_router() and mounted on a local
FastAPI app to isolate from the global app instance.
"""

from __future__ import annotations

import sqlite3
import uuid
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from rapidcull.api_envelope import register_handlers
from rapidcull.api_persons import configure_router, router
from rapidcull.schema import create_or_validate_schema

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _insert_person(db_path: Path, name: str) -> str:
    """Insert a person row and return its person_id."""
    person_id = str(uuid.uuid4())
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "INSERT INTO persons (person_id, name, created_at) VALUES (?, ?, datetime('now'))",
            (person_id, name),
        )
    return person_id


def _insert_image(db_path: Path) -> str:
    """Insert a minimal image row and return its image_id."""
    image_id = str(uuid.uuid4())
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "INSERT INTO images (image_id, path) VALUES (?, ?)",
            (image_id, f"/photos/{image_id}.jpg"),
        )
    return image_id


def _insert_face(db_path: Path, image_id: str, person_id: str | None) -> str:
    """Insert a face row linked to image and optionally a person."""
    face_id = str(uuid.uuid4())
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """INSERT INTO faces
               (face_id, image_id, person_id, embedding,
                bbox_x, bbox_y, bbox_w, bbox_h, detection_score)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (face_id, image_id, person_id, b"\x00" * 512, 0, 0, 50, 50, 0.99),
        )
    return face_id


def _make_client(db_path: Path) -> TestClient:
    configure_router(db_path)
    app = FastAPI()
    register_handlers(app)
    app.include_router(router)
    return TestClient(app, raise_server_exceptions=False)


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
    return _make_client(db_path)


# ---------------------------------------------------------------------------
# GET /api/v1/persons
# ---------------------------------------------------------------------------


class TestListPersons:
    def test_list_persons_empty(self, db_path: Path) -> None:
        client = _make_client(db_path)
        resp = client.get("/api/v1/persons")
        assert resp.status_code == 200
        body = resp.json()
        assert body["ok"] is True
        assert body["data"]["persons"] == []

    def test_list_persons_returns_persons(self, db_path: Path) -> None:
        person_id = _insert_person(db_path, "Alice")
        client = _make_client(db_path)
        resp = client.get("/api/v1/persons")
        assert resp.status_code == 200
        body = resp.json()
        assert body["ok"] is True
        persons = body["data"]["persons"]
        assert len(persons) == 1
        assert persons[0]["person_id"] == person_id
        assert persons[0]["name"] == "Alice"
        assert "created_at" in persons[0]
        assert isinstance(persons[0]["face_count"], int)


# ---------------------------------------------------------------------------
# PATCH /api/v1/persons/{person_id}
# ---------------------------------------------------------------------------


class TestPatchPerson:
    def test_patch_person_rename(self, db_path: Path) -> None:
        person_id = _insert_person(db_path, "Bob")
        client = _make_client(db_path)
        resp = client.patch(f"/api/v1/persons/{person_id}", json={"name": "Robert"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["ok"] is True
        assert body["data"]["person_id"] == person_id
        assert body["data"]["name"] == "Robert"

    def test_patch_person_not_found(self, db_path: Path) -> None:
        client = _make_client(db_path)
        resp = client.patch(f"/api/v1/persons/{uuid.uuid4()}", json={"name": "Nobody"})
        assert resp.status_code == 404
        body = resp.json()
        assert body["ok"] is False
        assert body["error"]["code"] == "PERSON_NOT_FOUND"


# ---------------------------------------------------------------------------
# POST /api/v1/persons/{person_id}/merge
# ---------------------------------------------------------------------------


class TestMergePersons:
    def test_merge_persons(self, db_path: Path) -> None:
        source_id = _insert_person(db_path, "Charlie")
        target_id = _insert_person(db_path, "Charles")
        image_id = _insert_image(db_path)
        _insert_face(db_path, image_id, source_id)
        _insert_face(db_path, image_id, source_id)
        client = _make_client(db_path)
        resp = client.post(
            f"/api/v1/persons/{source_id}/merge",
            json={"into_person_id": target_id},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["ok"] is True
        assert body["data"]["reassigned_count"] == 2
        assert body["data"]["deleted_person_id"] == source_id

    def test_merge_person_not_found(self, db_path: Path) -> None:
        client = _make_client(db_path)
        resp = client.post(
            f"/api/v1/persons/{uuid.uuid4()}/merge",
            json={"into_person_id": str(uuid.uuid4())},
        )
        assert resp.status_code == 404
        body = resp.json()
        assert body["ok"] is False
        assert body["error"]["code"] == "PERSON_NOT_FOUND"


# ---------------------------------------------------------------------------
# DELETE /api/v1/persons/{person_id}
# ---------------------------------------------------------------------------


class TestDeletePerson:
    def test_delete_person(self, db_path: Path) -> None:
        person_id = _insert_person(db_path, "Dave")
        client = _make_client(db_path)
        resp = client.delete(f"/api/v1/persons/{person_id}")
        assert resp.status_code == 200
        body = resp.json()
        assert body["ok"] is True
        assert body["data"]["deleted_person_id"] == person_id
        assert "deleted_face_count" in body["data"]
        assert "unlinked_face_count" in body["data"]

    def test_delete_person_not_found(self, db_path: Path) -> None:
        client = _make_client(db_path)
        resp = client.delete(f"/api/v1/persons/{uuid.uuid4()}")
        assert resp.status_code == 404
        body = resp.json()
        assert body["ok"] is False
        assert body["error"]["code"] == "PERSON_NOT_FOUND"
