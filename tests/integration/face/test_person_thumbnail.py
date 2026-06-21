"""Integration tests for GET /api/v1/persons/{person_id}/thumbnail."""

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


def _make_jpeg(path: Path, width: int = 64, height: int = 64) -> Path:
    """Write a minimal real JPEG using PIL so cv2 can decode it."""
    try:
        from PIL import Image  # type: ignore[import-untyped]
    except ImportError:
        pytest.skip("Pillow not installed")
    img = Image.new("RGB", (width, height), color=(180, 100, 60))
    img.save(str(path), "JPEG")
    return path


@pytest.fixture()
def tmp_lib(tmp_path: Path) -> Path:
    """Return a temp directory that serves as library_root."""
    lib = tmp_path / "library"
    lib.mkdir()
    return lib


@pytest.fixture()
def db_path(tmp_lib: Path) -> Path:
    path = tmp_lib / "test.db"
    create_or_validate_schema(path)
    return path


@pytest.fixture()
def client(db_path: Path, tmp_lib: Path) -> TestClient:
    app = create_app(db_path=db_path, library_root=tmp_lib)
    return TestClient(app)


@pytest.mark.integration
def test_thumbnail_returns_webp(
    client: TestClient, db_path: Path, tmp_lib: Path
) -> None:
    """Endpoint returns 200 image/webp with non-empty body for a person with faces."""
    pytest.importorskip("cv2")

    # Create a real image file.
    img_file = tmp_lib / "photo.jpg"
    _make_jpeg(img_file)

    # Insert image record.
    record = create_image_record(db_path, img_file)

    # Insert person + face.
    person_id = str(uuid.uuid4())
    face_id = str(uuid.uuid4())
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "INSERT INTO persons (person_id, name, created_at) VALUES (?, ?, ?)",
            (person_id, "Alice", datetime.now(UTC).isoformat()),
        )
        conn.execute(
            """INSERT INTO faces
               (face_id, image_id, person_id, embedding, bbox_x, bbox_y, bbox_w, bbox_h, detection_score)
               VALUES (?, ?, ?, ?, 5, 5, 40, 40, 0.95)""",
            (face_id, record.image_id, person_id, _make_embedding()),
        )

    resp = client.get(f"/api/v1/persons/{person_id}/thumbnail")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "image/webp"
    assert len(resp.content) >= 50


@pytest.mark.integration
def test_thumbnail_cached_same_mtime(
    client: TestClient, db_path: Path, tmp_lib: Path
) -> None:
    """Second call returns the cached file (same mtime)."""
    pytest.importorskip("cv2")

    img_file = tmp_lib / "photo2.jpg"
    _make_jpeg(img_file)
    record = create_image_record(db_path, img_file)

    person_id = str(uuid.uuid4())
    face_id = str(uuid.uuid4())
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "INSERT INTO persons (person_id, name, created_at) VALUES (?, ?, ?)",
            (person_id, "Bob", datetime.now(UTC).isoformat()),
        )
        conn.execute(
            """INSERT INTO faces
               (face_id, image_id, person_id, embedding, bbox_x, bbox_y, bbox_w, bbox_h, detection_score)
               VALUES (?, ?, ?, ?, 10, 10, 30, 30, 0.90)""",
            (face_id, record.image_id, person_id, _make_embedding()),
        )

    # First call — generates cache file.
    r1 = client.get(f"/api/v1/persons/{person_id}/thumbnail")
    assert r1.status_code == 200

    cache_path = tmp_lib / ".rapidcull" / "face_thumbs" / f"{face_id}.webp"
    assert cache_path.exists()
    mtime1 = cache_path.stat().st_mtime

    # Second call — should serve from cache (mtime unchanged).
    r2 = client.get(f"/api/v1/persons/{person_id}/thumbnail")
    assert r2.status_code == 200
    assert cache_path.stat().st_mtime == mtime1


@pytest.mark.integration
def test_thumbnail_404_no_faces(client: TestClient, db_path: Path) -> None:
    """404 for a person with no faces assigned."""
    person_id = str(uuid.uuid4())
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "INSERT INTO persons (person_id, name, created_at) VALUES (?, ?, ?)",
            (person_id, "Empty", datetime.now(UTC).isoformat()),
        )

    resp = client.get(f"/api/v1/persons/{person_id}/thumbnail")
    assert resp.status_code == 404


@pytest.mark.integration
def test_thumbnail_404_unknown_person(client: TestClient) -> None:
    """404 for a totally unknown person_id."""
    resp = client.get(f"/api/v1/persons/{uuid.uuid4()}/thumbnail")
    assert resp.status_code == 404
