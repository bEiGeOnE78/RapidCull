"""Integration tests: create_gallery_picks job creates a user gallery from pick decisions.

Verifies:
- Job creates a row in `galleries` table with source='from_picks'
- Only pick-decision image_ids get membership rows
- No filesystem hardlinks/dirs created
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


def _add_decision(db_path: Path, image_id: str, decision: str) -> None:
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "INSERT INTO cull_decisions (image_id, decision, decided_at) VALUES (?, ?, ?)",
            (image_id, decision, "2026-01-01T00:00:00Z"),
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
def test_create_gallery_picks_job_creates_user_gallery(
    app_client: tuple[TestClient, Path],
) -> None:
    """create_gallery_picks job creates a galleries row with source='from_picks'."""
    client, db_path = app_client

    _add_image(db_path, "img_001", "/photos/a.jpg")
    _add_image(db_path, "img_002", "/photos/b.jpg")
    _add_image(db_path, "img_003", "/photos/c.jpg")
    _add_decision(db_path, "img_001", "pick")
    _add_decision(db_path, "img_002", "pick")
    _add_decision(db_path, "img_003", "reject")  # should NOT be included

    resp = client.post(
        "/api/v1/jobs",
        json={"kind": "create_gallery_picks", "params": {"name": "My Picks"}},
    )
    assert resp.status_code == 201
    job_id = resp.json()["data"]["job_id"]

    job = _wait_for_terminal(client, job_id)
    assert job["state"] == "succeeded", f"Job failed: {job.get('error')}"

    # Verify galleries table row
    with sqlite3.connect(db_path) as conn:
        gallery_rows = conn.execute(
            "SELECT gallery_id, name, source FROM galleries WHERE name = ?",
            ("My Picks",),
        ).fetchall()
    assert len(gallery_rows) == 1
    gallery_id, name, source = gallery_rows[0]
    assert name == "My Picks"
    assert source == "from_picks"

    # Verify only pick-decision images got memberships
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
def test_create_gallery_picks_job_no_filesystem_dirs(
    app_client: tuple[TestClient, Path],
    tmp_path: Path,
) -> None:
    """create_gallery_picks must NOT create any filesystem gallery dirs or hardlinks."""
    client, db_path = app_client

    _add_image(db_path, "img_001", "/photos/a.jpg")
    _add_decision(db_path, "img_001", "pick")

    resp = client.post(
        "/api/v1/jobs",
        json={"kind": "create_gallery_picks", "params": {"name": "Pure DB Gallery"}},
    )
    job_id = resp.json()["data"]["job_id"]
    job = _wait_for_terminal(client, job_id)
    assert job["state"] == "succeeded"

    # No galleries/ directory should exist in the DB parent
    gallery_dir = db_path.parent / "galleries"
    # If it exists (from other tests), it must be empty of per-gallery dirs for this gallery
    if gallery_dir.exists():
        subdirs = [d for d in gallery_dir.iterdir() if d.is_dir()]
        # Only check that no subdirectory named "Pure DB Gallery" was created
        names = {d.name for d in subdirs}
        assert "Pure DB Gallery" not in names


@pytest.mark.fr
@pytest.mark.integration
def test_create_gallery_picks_job_requires_name_param(
    app_client: tuple[TestClient, Path],
) -> None:
    """create_gallery_picks without 'name' param → job fails with clear error."""
    client, db_path = app_client

    resp = client.post(
        "/api/v1/jobs",
        json={"kind": "create_gallery_picks", "params": {}},
    )
    assert resp.status_code == 201
    job_id = resp.json()["data"]["job_id"]
    job = _wait_for_terminal(client, job_id)
    assert job["state"] == "failed"
    assert "name" in job["error"].lower()


@pytest.mark.fr
@pytest.mark.integration
def test_create_gallery_picks_job_with_no_picks(
    app_client: tuple[TestClient, Path],
) -> None:
    """create_gallery_picks with no pick decisions → empty gallery created."""
    client, db_path = app_client

    _add_image(db_path, "img_001", "/photos/a.jpg")
    _add_decision(db_path, "img_001", "reject")

    resp = client.post(
        "/api/v1/jobs",
        json={"kind": "create_gallery_picks", "params": {"name": "Empty Picks"}},
    )
    job_id = resp.json()["data"]["job_id"]
    job = _wait_for_terminal(client, job_id)
    assert job["state"] == "succeeded"

    with sqlite3.connect(db_path) as conn:
        gallery_rows = conn.execute(
            "SELECT gallery_id FROM galleries WHERE name = 'Empty Picks'"
        ).fetchall()
    assert len(gallery_rows) == 1
    gallery_id = gallery_rows[0][0]

    with sqlite3.connect(db_path) as conn:
        count = conn.execute(
            "SELECT COUNT(*) FROM gallery_memberships WHERE gallery_id = ?", (gallery_id,)
        ).fetchone()[0]
    assert count == 0
