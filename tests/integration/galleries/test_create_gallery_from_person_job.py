"""Integration tests: create_gallery_from_person job creates a user gallery from face data.

Verifies:
- Job creates a row in `galleries` table with source='from_person'
- Only distinct image_ids linked to the person get membership rows
- Person with 0 faces → empty gallery (no error)
- Missing 'name' or 'person_id' param → job fails with ValueError
"""

from __future__ import annotations

import sqlite3
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from rapidcull.api import create_app
from rapidcull.api_jobs import configure_executor
from rapidcull.jobs import get_job_store
from rapidcull.schema import create_or_validate_schema

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _add_image(db_path: Path, image_id: str, path: str) -> None:
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "INSERT INTO images (image_id, path) VALUES (?, ?)",
            (image_id, path),
        )


def _add_person(db_path: Path, person_id: str, name: str) -> None:
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "INSERT INTO persons (person_id, name, created_at) VALUES (?, ?, ?)",
            (person_id, name, "2026-01-01T00:00:00Z"),
        )


def _add_face(db_path: Path, face_id: str, image_id: str, person_id: str) -> None:
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "INSERT INTO faces"
            " (face_id, image_id, person_id, embedding, bbox_x, bbox_y, bbox_w, bbox_h, detection_score)"
            " VALUES (?, ?, ?, ?, 0, 0, 10, 10, 0.99)",
            (face_id, image_id, person_id, b"\x00" * 16),
        )


def _wait_for_terminal(client: TestClient, job_id: str, timeout: float = 10.0) -> dict:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        resp = client.get(f"/api/v1/jobs/{job_id}")
        data = resp.json()["data"]
        if data["state"] in ("succeeded", "failed", "cancelled"):
            return data  # type: ignore[return-value]
        time.sleep(0.05)
    raise TimeoutError(f"Job {job_id} did not reach terminal state within {timeout}s")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _clear_job_store() -> pytest.Generator[None, None, None]:
    get_job_store().clear()
    yield
    configure_executor(None)  # type: ignore[arg-type]
    get_job_store().clear()


@pytest.fixture()
def app_client(tmp_path: Path) -> tuple[TestClient, Path]:
    db_path = tmp_path / "test.db"
    create_or_validate_schema(db_path)
    client = TestClient(create_app(db_path=db_path))
    return client, db_path


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.fr
@pytest.mark.integration
def test_create_gallery_from_person_creates_gallery(
    app_client: tuple[TestClient, Path],
) -> None:
    """create_gallery_from_person creates a galleries row with source='from_person'."""
    client, db_path = app_client

    _add_image(db_path, "img_001", "/photos/a.jpg")
    _add_image(db_path, "img_002", "/photos/b.jpg")
    _add_image(db_path, "img_003", "/photos/c.jpg")
    _add_person(db_path, "person_001", "Alice")

    # img_001 has 2 faces of the same person (DISTINCT must collapse to 1 image)
    _add_face(db_path, "face_001", "img_001", "person_001")
    _add_face(db_path, "face_002", "img_001", "person_001")
    # img_002 has 1 face of the person
    _add_face(db_path, "face_003", "img_002", "person_001")
    # img_003 has no face of this person → must NOT be included

    resp = client.post(
        "/api/v1/jobs",
        json={
            "kind": "create_gallery_from_person",
            "params": {"name": "Alice Gallery", "person_id": "person_001"},
        },
    )
    assert resp.status_code == 201
    job_id = resp.json()["data"]["job_id"]

    job = _wait_for_terminal(client, job_id)
    assert job["state"] == "succeeded", f"Job failed: {job.get('error')}"

    result = job["result"]
    assert result["image_count"] == 2
    assert result["person_id"] == "person_001"

    # Verify galleries table row
    with sqlite3.connect(db_path) as conn:
        gallery_rows = conn.execute(
            "SELECT gallery_id, name, source FROM galleries WHERE name = ?",
            ("Alice Gallery",),
        ).fetchall()
    assert len(gallery_rows) == 1
    gallery_id, name, source = gallery_rows[0]
    assert name == "Alice Gallery"
    assert source == "from_person"

    # Verify membership: exactly img_001 and img_002
    with sqlite3.connect(db_path) as conn:
        member_rows = conn.execute(
            "SELECT image_id FROM gallery_memberships WHERE gallery_id = ? ORDER BY image_id",
            (gallery_id,),
        ).fetchall()
    member_ids = {row[0] for row in member_rows}
    assert member_ids == {"img_001", "img_002"}
    assert "img_003" not in member_ids


@pytest.mark.fr
@pytest.mark.integration
def test_create_gallery_from_person_zero_faces(
    app_client: tuple[TestClient, Path],
) -> None:
    """create_gallery_from_person with person who has no faces → empty gallery, no error."""
    client, db_path = app_client

    _add_image(db_path, "img_001", "/photos/a.jpg")
    _add_person(db_path, "person_002", "Bob")
    # No face rows for Bob

    resp = client.post(
        "/api/v1/jobs",
        json={
            "kind": "create_gallery_from_person",
            "params": {"name": "Empty Person Gallery", "person_id": "person_002"},
        },
    )
    assert resp.status_code == 201
    job_id = resp.json()["data"]["job_id"]

    job = _wait_for_terminal(client, job_id)
    assert job["state"] == "succeeded"
    assert job["result"]["image_count"] == 0

    with sqlite3.connect(db_path) as conn:
        gallery_rows = conn.execute(
            "SELECT gallery_id FROM galleries WHERE name = 'Empty Person Gallery'"
        ).fetchall()
    assert len(gallery_rows) == 1
    gallery_id = gallery_rows[0][0]

    with sqlite3.connect(db_path) as conn:
        count = conn.execute(
            "SELECT COUNT(*) FROM gallery_memberships WHERE gallery_id = ?", (gallery_id,)
        ).fetchone()[0]
    assert count == 0


@pytest.mark.fr
@pytest.mark.integration
def test_create_gallery_from_person_requires_name(
    app_client: tuple[TestClient, Path],
) -> None:
    """create_gallery_from_person without 'name' param → job fails."""
    client, db_path = app_client

    resp = client.post(
        "/api/v1/jobs",
        json={"kind": "create_gallery_from_person", "params": {"person_id": "person_001"}},
    )
    assert resp.status_code == 201
    job_id = resp.json()["data"]["job_id"]
    job = _wait_for_terminal(client, job_id)
    assert job["state"] == "failed"
    assert "name" in job["error"].lower()


@pytest.mark.fr
@pytest.mark.integration
def test_create_gallery_from_person_requires_person_id(
    app_client: tuple[TestClient, Path],
) -> None:
    """create_gallery_from_person without 'person_id' param → job fails."""
    client, db_path = app_client

    resp = client.post(
        "/api/v1/jobs",
        json={"kind": "create_gallery_from_person", "params": {"name": "No Person"}},
    )
    assert resp.status_code == 201
    job_id = resp.json()["data"]["job_id"]
    job = _wait_for_terminal(client, job_id)
    assert job["state"] == "failed"
    assert "person_id" in job["error"].lower()
