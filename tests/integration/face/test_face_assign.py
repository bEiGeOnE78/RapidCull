"""Integration tests for POST /api/v1/faces/{face_id}/assign."""

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


def _make_embedding(seed: float = 0.5, dims: int = 512) -> bytes:
    return struct.pack(f"{dims}f", *[seed] * dims)


@pytest.fixture()
def db_path(tmp_path: Path) -> Path:
    path = tmp_path / "test.db"
    create_or_validate_schema(path)
    return path


@pytest.fixture()
def client(db_path: Path) -> TestClient:
    app = create_app(db_path=db_path)
    return TestClient(app)


def _insert_person(db_path: Path, name: str = "Alice") -> str:
    person_id = str(uuid.uuid4())
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "INSERT INTO persons (person_id, name, created_at) VALUES (?, ?, ?)",
            (person_id, name, datetime.now(UTC).isoformat()),
        )
    return person_id


def _insert_face(
    db_path: Path, tmp_path: Path, person_id: str | None = None
) -> tuple[str, str]:
    """Insert image + face row; return (image_id, face_id)."""
    img = tmp_path / f"{uuid.uuid4()}.jpg"
    img.write_bytes(b"\xff\xd8\xff")
    record = create_image_record(db_path, img)

    face_id = str(uuid.uuid4())
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """INSERT INTO faces
               (face_id, image_id, person_id, embedding, bbox_x, bbox_y, bbox_w, bbox_h, detection_score)
               VALUES (?, ?, ?, ?, 0, 0, 50, 50, 0.85)""",
            (face_id, record.image_id, person_id, _make_embedding()),
        )
    return record.image_id, face_id


@pytest.mark.integration
def test_assign_face_to_person(
    client: TestClient, db_path: Path, tmp_path: Path
) -> None:
    """POST assign with valid person_id → 200, DB row updated."""
    person_id = _insert_person(db_path)
    _, face_id = _insert_face(db_path, tmp_path)

    resp = client.post(
        f"/api/v1/faces/{face_id}/assign",
        json={"person_id": person_id},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["data"]["ok"] is True
    assert data["data"]["face_id"] == face_id
    assert data["data"]["person_id"] == person_id

    # Verify DB.
    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            "SELECT person_id FROM faces WHERE face_id = ?", (face_id,)
        ).fetchone()
    assert row is not None
    assert row[0] == person_id


@pytest.mark.integration
def test_assign_face_unassign(
    client: TestClient, db_path: Path, tmp_path: Path
) -> None:
    """POST with person_id: null → 200, DB row set to NULL."""
    person_id = _insert_person(db_path)
    _, face_id = _insert_face(db_path, tmp_path, person_id=person_id)

    resp = client.post(
        f"/api/v1/faces/{face_id}/assign",
        json={"person_id": None},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["data"]["person_id"] is None

    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            "SELECT person_id FROM faces WHERE face_id = ?", (face_id,)
        ).fetchone()
    assert row is not None
    assert row[0] is None


@pytest.mark.integration
def test_assign_face_bad_face_id(client: TestClient) -> None:
    """POST with bad face_id → 404."""
    resp = client.post(
        f"/api/v1/faces/{uuid.uuid4()}/assign",
        json={"person_id": None},
    )
    assert resp.status_code == 404


@pytest.mark.integration
def test_assign_face_bad_person_id(
    client: TestClient, db_path: Path, tmp_path: Path
) -> None:
    """POST with bad person_id (unknown) → 404."""
    _, face_id = _insert_face(db_path, tmp_path)

    resp = client.post(
        f"/api/v1/faces/{face_id}/assign",
        json={"person_id": str(uuid.uuid4())},
    )
    assert resp.status_code == 404
