"""Integration tests for FR-028: DELETE /api/v1/persons/{person_id} endpoint."""

from __future__ import annotations

import sqlite3
import struct
import uuid
from datetime import UTC, datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from rapidcull.api import create_app
from rapidcull.identity import create_image_record
from rapidcull.schema import create_or_validate_schema


def _make_embedding(dims: int = 512) -> bytes:
    return struct.pack(f"{dims}f", *[0.5] * dims)


@pytest.fixture()
def tmp_library(tmp_path: Path) -> Path:
    lib = tmp_path / "library"
    lib.mkdir()
    return lib


@pytest.fixture()
def db_path(tmp_library: Path) -> Path:
    path = tmp_library / "test.db"
    create_or_validate_schema(path)
    return path


@pytest.fixture()
def client(db_path: Path, tmp_library: Path) -> TestClient:
    from rapidcull import api_persons

    api_persons.configure_router(db_path, library_root=tmp_library)
    app = create_app(db_path, library_root=tmp_library)
    return TestClient(app, raise_server_exceptions=True)


def _insert_person(db_path: Path, name: str) -> str:
    pid = str(uuid.uuid4())
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "INSERT INTO persons (person_id, name, created_at) VALUES (?, ?, ?)",
            (pid, name, datetime.now(UTC).isoformat()),
        )
    return pid


def _insert_image(db_path: Path, tmp_library: Path, name: str = "img.jpg") -> str:
    img = tmp_library / name
    img.write_bytes(b"\xff\xd8\xff")
    record = create_image_record(db_path, img)
    return record.image_id


def _insert_face(db_path: Path, image_id: str, person_id: str, face_id: str) -> None:
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """INSERT INTO faces (face_id, image_id, person_id, embedding,
               bbox_x, bbox_y, bbox_w, bbox_h, detection_score)
               VALUES (?, ?, ?, ?, 0, 0, 80, 100, 0.95)""",
            (face_id, image_id, person_id, _make_embedding()),
        )


def _make_thumb(tmp_library: Path, face_id: str) -> Path:
    """Write a dummy thumb file and return its path."""
    thumb_dir = tmp_library / ".rapidcull" / "face_thumbs"
    thumb_dir.mkdir(parents=True, exist_ok=True)
    p = thumb_dir / f"{face_id}.webp"
    p.write_bytes(b"WEBP")
    return p


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.fr
@pytest.mark.integration
def test_delete_person_without_flag_unlinks_faces(
    client: TestClient, db_path: Path, tmp_library: Path
) -> None:
    """DELETE without ?delete_embeddings → 200, faces unlinked, thumbs kept."""
    image_id = _insert_image(db_path, tmp_library)
    pid = _insert_person(db_path, "Alice")
    face_id = "face-api-unlink-1"
    _insert_face(db_path, image_id, pid, face_id)
    thumb = _make_thumb(tmp_library, face_id)

    resp = client.delete(f"/api/v1/persons/{pid}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["ok"] is True
    assert body["data"]["deleted_person_id"] == pid
    assert body["data"]["delete_embeddings"] is False
    assert body["data"]["unlinked_face_count"] == 1
    assert body["data"]["deleted_face_count"] == 0

    # person row gone
    with sqlite3.connect(db_path) as conn:
        assert conn.execute("SELECT 1 FROM persons WHERE person_id = ?", (pid,)).fetchone() is None
        # face row preserved, person_id nulled
        row = conn.execute("SELECT person_id FROM faces WHERE face_id = ?", (face_id,)).fetchone()
        assert row is not None
        assert row[0] is None

    # thumb NOT deleted
    assert thumb.exists()


@pytest.mark.fr
@pytest.mark.integration
def test_delete_person_with_embeddings_removes_faces_and_thumbs(
    client: TestClient, db_path: Path, tmp_library: Path
) -> None:
    """DELETE ?delete_embeddings=true → 200, face rows deleted, thumbs unlinked."""
    image_id = _insert_image(db_path, tmp_library)
    pid = _insert_person(db_path, "Bob")
    face_id_a = "face-api-del-a"
    face_id_b = "face-api-del-b"
    _insert_face(db_path, image_id, pid, face_id_a)
    _insert_face(db_path, image_id, pid, face_id_b)
    thumb_a = _make_thumb(tmp_library, face_id_a)
    thumb_b = _make_thumb(tmp_library, face_id_b)

    resp = client.delete(f"/api/v1/persons/{pid}?delete_embeddings=true")
    assert resp.status_code == 200
    body = resp.json()
    assert body["ok"] is True
    assert body["data"]["delete_embeddings"] is True
    assert body["data"]["deleted_face_count"] == 2
    assert body["data"]["unlinked_face_count"] == 0

    with sqlite3.connect(db_path) as conn:
        assert conn.execute("SELECT 1 FROM persons WHERE person_id = ?", (pid,)).fetchone() is None
        assert conn.execute("SELECT COUNT(*) FROM faces WHERE face_id IN (?, ?)", (face_id_a, face_id_b)).fetchone()[0] == 0

    assert not thumb_a.exists()
    assert not thumb_b.exists()


@pytest.mark.fr
@pytest.mark.integration
def test_delete_person_with_embeddings_missing_thumb_ok(
    client: TestClient, db_path: Path, tmp_library: Path
) -> None:
    """DELETE with embeddings when no thumb exists → still 200, no crash."""
    image_id = _insert_image(db_path, tmp_library)
    pid = _insert_person(db_path, "Carol")
    _insert_face(db_path, image_id, pid, "face-no-thumb")

    resp = client.delete(f"/api/v1/persons/{pid}?delete_embeddings=true")
    assert resp.status_code == 200
    assert resp.json()["ok"] is True


@pytest.mark.fr
@pytest.mark.integration
def test_delete_person_not_found_returns_404(client: TestClient) -> None:
    """DELETE nonexistent person → 404 with PERSON_NOT_FOUND code."""
    resp = client.delete("/api/v1/persons/nonexistent-id")
    assert resp.status_code == 404
    body = resp.json()
    assert body["ok"] is False
    assert body["error"]["code"] == "PERSON_NOT_FOUND"
