"""Integration tests: GET /api/v1/images/search

Covers:
  - person filter (person=Maya)
  - numeric filter (iso>800)
  - compound AND filter
  - bad query syntax → 400 with error detail
  - empty query → 200 all images
  - pagination (offset + limit)
  - zero results → 200, empty list, total_count=0
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


def _insert_image(
    conn: sqlite3.Connection,
    path: str,
    metadata: dict,
) -> str:
    image_id = uuid.uuid4().hex
    conn.execute(
        "INSERT INTO images (image_id, path, metadata) VALUES (?, ?, ?)",
        (image_id, path, json.dumps(metadata)),
    )
    return image_id


def _insert_person(conn: sqlite3.Connection, name: str) -> str:
    person_id = uuid.uuid4().hex
    conn.execute(
        "INSERT INTO persons (person_id, name, created_at) VALUES (?, ?, '2026-01-01T00:00:00')",
        (person_id, name),
    )
    return person_id


def _insert_face(conn: sqlite3.Connection, image_id: str, person_id: str) -> None:
    face_id = uuid.uuid4().hex
    conn.execute(
        """INSERT INTO faces
           (face_id, image_id, person_id, embedding, bbox_x, bbox_y, bbox_w, bbox_h, detection_score)
           VALUES (?, ?, ?, X'00', 0, 0, 10, 10, 0.99)""",
        (face_id, image_id, person_id),
    )


@pytest.fixture()
def client_and_db(tmp_path: Path):
    db_path = tmp_path / "test.db"
    create_or_validate_schema(db_path)

    with sqlite3.connect(db_path) as conn:
        # Image 1: Maya, low ISO
        img1 = _insert_image(conn, "/photos/img1.jpg", {"iso": 100, "date": "2024-01-01"})
        # Image 2: Maya, high ISO
        img2 = _insert_image(conn, "/photos/img2.jpg", {"iso": 1600, "date": "2024-06-15"})
        # Image 3: Bob, high ISO
        img3 = _insert_image(conn, "/photos/img3.jpg", {"iso": 3200, "date": "2024-09-01"})
        # Image 4: no person, medium ISO
        img4 = _insert_image(conn, "/photos/img4.jpg", {"iso": 400, "date": "2024-03-10"})
        # Image 5: no person, no metadata
        img5 = _insert_image(conn, "/photos/img5.jpg", {})

        maya_id = _insert_person(conn, "Maya")
        bob_id = _insert_person(conn, "Bob")

        _insert_face(conn, img1, maya_id)
        _insert_face(conn, img2, maya_id)
        _insert_face(conn, img3, bob_id)

        conn.commit()

    client = TestClient(create_app(db_path=db_path))
    return client, db_path


# ---------------------------------------------------------------------------
# Person filter
# ---------------------------------------------------------------------------


@pytest.mark.fr
@pytest.mark.integration
def test_search_person_maya(client_and_db) -> None:
    """GET /api/v1/images/search?query=person=Maya → only Maya's images."""
    client, _ = client_and_db
    resp = client.get("/api/v1/images/search", params={"query": "person=Maya"})
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["total_count"] == 2
    paths = {img["path"] for img in data["images"]}
    assert paths == {"/photos/img1.jpg", "/photos/img2.jpg"}


# ---------------------------------------------------------------------------
# ISO numeric filter
# ---------------------------------------------------------------------------


@pytest.mark.fr
@pytest.mark.integration
def test_search_iso_gt_800(client_and_db) -> None:
    """GET /api/v1/images/search?query=iso>800 → images with ISO > 800."""
    client, _ = client_and_db
    resp = client.get("/api/v1/images/search", params={"query": "iso>800"})
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["total_count"] == 2
    paths = {img["path"] for img in data["images"]}
    assert paths == {"/photos/img2.jpg", "/photos/img3.jpg"}


# ---------------------------------------------------------------------------
# Compound AND filter
# ---------------------------------------------------------------------------


@pytest.mark.fr
@pytest.mark.integration
def test_search_person_and_iso(client_and_db) -> None:
    """GET query=person=Maya AND iso>800 → intersection: only img2."""
    client, _ = client_and_db
    resp = client.get("/api/v1/images/search", params={"query": "person=Maya AND iso>800"})
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["total_count"] == 1
    assert data["images"][0]["path"] == "/photos/img2.jpg"


# ---------------------------------------------------------------------------
# Bad syntax → 400
# ---------------------------------------------------------------------------


@pytest.mark.fr
@pytest.mark.integration
def test_search_bad_syntax_returns_400(client_and_db) -> None:
    """Invalid query syntax → 400 with error detail."""
    client, _ = client_and_db
    resp = client.get("/api/v1/images/search", params={"query": "AND bogus"})
    assert resp.status_code == 400
    body = resp.json()
    assert body["ok"] is False
    assert body["error"]["code"] == "QUERY_PARSE_ERROR"
    assert "details" in body["error"]
    detail = body["error"]["details"]
    assert "code" in detail
    assert "message" in detail
    assert "suggestions" in detail
    assert "token" in detail


# ---------------------------------------------------------------------------
# Empty query → all images
# ---------------------------------------------------------------------------


@pytest.mark.fr
@pytest.mark.integration
def test_search_empty_query_returns_all(client_and_db) -> None:
    """Empty query string → 200 with all images."""
    client, _ = client_and_db
    resp = client.get("/api/v1/images/search", params={"query": ""})
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["total_count"] == 5
    assert data["query_echo"] == ""


# ---------------------------------------------------------------------------
# Pagination
# ---------------------------------------------------------------------------


@pytest.mark.fr
@pytest.mark.integration
def test_search_pagination(client_and_db) -> None:
    """Pagination: offset=0 limit=2 returns 2 items, total_count reflects full match set."""
    client, _ = client_and_db
    resp = client.get("/api/v1/images/search", params={"query": "", "offset": 0, "limit": 2})
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["total_count"] == 5
    assert len(data["images"]) == 2

    resp2 = client.get("/api/v1/images/search", params={"query": "", "offset": 2, "limit": 2})
    assert resp2.status_code == 200
    data2 = resp2.json()["data"]
    assert data2["total_count"] == 5
    assert len(data2["images"]) == 2

    # Pages don't overlap
    ids1 = {img["image_id"] for img in data["images"]}
    ids2 = {img["image_id"] for img in data2["images"]}
    assert ids1.isdisjoint(ids2)


# ---------------------------------------------------------------------------
# Zero results
# ---------------------------------------------------------------------------


@pytest.mark.fr
@pytest.mark.integration
def test_search_zero_results(client_and_db) -> None:
    """Query matching nobody → 200, empty list, total_count=0."""
    client, _ = client_and_db
    resp = client.get("/api/v1/images/search", params={"query": "person=NoSuchPerson"})
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["total_count"] == 0
    assert data["images"] == []


# ---------------------------------------------------------------------------
# Response shape
# ---------------------------------------------------------------------------


@pytest.mark.fr
@pytest.mark.integration
def test_search_response_shape(client_and_db) -> None:
    """Each image in results has the expected fields matching gallery-images shape."""
    client, _ = client_and_db
    resp = client.get("/api/v1/images/search", params={"query": "person=Maya"})
    assert resp.status_code == 200
    images = resp.json()["data"]["images"]
    assert len(images) > 0
    for img in images:
        assert "image_id" in img
        assert "path" in img
        assert "thumbnail_path" in img
        assert "display_path" in img
        assert "full_path" in img
        assert "decision" in img
    assert "query_echo" in resp.json()["data"]
