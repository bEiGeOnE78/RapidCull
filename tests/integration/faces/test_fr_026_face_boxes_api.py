"""Integration tests for FR-026: Face boxes API endpoint."""

from __future__ import annotations

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


@pytest.mark.fr
@pytest.mark.integration
def test_fr_026_face_boxes_empty(client: TestClient, db_path: Path, tmp_path: Path) -> None:
    """GET /api/v1/images/{image_id}/faces returns empty list when no faces stored."""
    img = tmp_path / "a.jpg"
    img.write_bytes(b"\xff\xd8\xff")
    record = create_image_record(db_path, img)

    resp = client.get(f"/api/v1/images/{record.image_id}/faces")
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert data["data"]["image_id"] == record.image_id
    assert data["data"]["faces"] == []


@pytest.mark.fr
@pytest.mark.integration
def test_fr_026_face_boxes_with_faces(client: TestClient, db_path: Path, tmp_path: Path) -> None:
    """GET /api/v1/images/{image_id}/faces returns bbox and person_id for stored faces."""
    import sqlite3

    img = tmp_path / "a.jpg"
    img.write_bytes(b"\xff\xd8\xff")
    record = create_image_record(db_path, img)

    # Insert person + face directly
    person_id = str(uuid.uuid4())
    face_id = str(uuid.uuid4())
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "INSERT INTO persons (person_id, name, created_at) VALUES (?, ?, ?)",
            (person_id, "Alice", datetime.now(UTC).isoformat()),
        )
        conn.execute(
            """INSERT INTO faces (face_id, image_id, person_id, embedding,
               bbox_x, bbox_y, bbox_w, bbox_h, detection_score)
               VALUES (?, ?, ?, ?, 10, 20, 80, 100, 0.97)""",
            (face_id, record.image_id, person_id, _make_embedding()),
        )

    resp = client.get(f"/api/v1/images/{record.image_id}/faces")
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    faces = data["data"]["faces"]
    assert len(faces) == 1
    face = faces[0]
    assert face["face_id"] == face_id
    assert face["person_id"] == person_id
    assert face["person_name"] == "Alice"
    assert face["bbox"] == {"x": 10, "y": 20, "w": 80, "h": 100}
    assert face["score"] == pytest.approx(0.97, abs=0.01)


@pytest.mark.fr
@pytest.mark.integration
def test_fr_026_face_boxes_unknown_image(client: TestClient) -> None:
    """GET /api/v1/images/{image_id}/faces returns 404 for unknown image_id."""
    resp = client.get("/api/v1/images/nonexistent-id/faces")
    assert resp.status_code == 404
