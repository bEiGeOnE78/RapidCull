"""Integration tests for FR-025, FR-028: Person identity CRUD and deletion."""

from __future__ import annotations

import sqlite3
import struct
from datetime import UTC
from pathlib import Path

import pytest

from rapidcull.adapters.insightface_adapter import DetectedFace, FaceDetectionSuccess
from rapidcull.identity import create_image_record
from rapidcull.models import PersonMergeResult, PersonRecord
from rapidcull.persons import delete_person, list_persons, merge_persons, rename_person
from rapidcull.schema import create_or_validate_schema


def _make_embedding(seed: float = 0.5, dims: int = 512) -> bytes:
    return struct.pack(f"{dims}f", *[seed] * dims)


class _ConstDetector:
    def __init__(self, embedding_seed: float = 0.5) -> None:
        self._seed = embedding_seed

    def detect(self, image_path: Path) -> FaceDetectionSuccess:
        return FaceDetectionSuccess(
            faces=[
                DetectedFace(
                    bbox_x=0,
                    bbox_y=0,
                    bbox_w=80,
                    bbox_h=100,
                    embedding=_make_embedding(self._seed),
                    detection_score=0.95,
                )
            ]
        )

    @property
    def pipeline_available(self) -> bool:
        return True


@pytest.fixture()
def db_path(tmp_path: Path) -> Path:
    path = tmp_path / "test.db"
    create_or_validate_schema(path)
    return path


def _add_person(db_path: Path, name: str) -> str:
    """Insert a person directly and return person_id."""
    import uuid
    from datetime import datetime

    person_id = str(uuid.uuid4())
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "INSERT INTO persons (person_id, name, created_at) VALUES (?, ?, ?)",
            (person_id, name, datetime.now(UTC).isoformat()),
        )
    return person_id


def _add_face_for_person(db_path: Path, person_id: str, face_id: str, image_id: str) -> None:
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """INSERT INTO faces (face_id, image_id, person_id, embedding,
               bbox_x, bbox_y, bbox_w, bbox_h, detection_score)
               VALUES (?, ?, ?, ?, 0, 0, 80, 100, 0.95)""",
            (face_id, image_id, person_id, _make_embedding()),
        )


def _add_image(db_path: Path, tmp_path: Path, name: str = "a.jpg") -> str:
    img = tmp_path / name
    img.write_bytes(b"\xff\xd8\xff")
    record = create_image_record(db_path, img)
    return record.image_id


# ---------------------------------------------------------------------------
# list_persons
# ---------------------------------------------------------------------------


@pytest.mark.fr
@pytest.mark.integration
def test_fr_025_list_persons_empty(db_path: Path) -> None:
    assert list_persons(db_path) == []


@pytest.mark.fr
@pytest.mark.integration
def test_fr_025_list_persons_returns_records(db_path: Path) -> None:
    _add_person(db_path, "Alice")
    _add_person(db_path, "Bob")
    persons = list_persons(db_path)
    assert len(persons) == 2
    names = {p.name for p in persons}
    assert names == {"Alice", "Bob"}
    assert all(isinstance(p, PersonRecord) for p in persons)


# ---------------------------------------------------------------------------
# rename_person
# ---------------------------------------------------------------------------


@pytest.mark.fr
@pytest.mark.integration
def test_fr_025_rename_person(db_path: Path) -> None:
    pid = _add_person(db_path, "Alice")
    result = rename_person(db_path, pid, "Alicia")
    assert isinstance(result, PersonRecord)
    assert result.name == "Alicia"
    assert result.person_id == pid


@pytest.mark.fr
@pytest.mark.integration
def test_fr_025_rename_person_not_found_raises(db_path: Path) -> None:
    with pytest.raises(ValueError, match="not found"):
        rename_person(db_path, "nonexistent-id", "X")


# ---------------------------------------------------------------------------
# merge_persons
# ---------------------------------------------------------------------------


@pytest.mark.fr
@pytest.mark.integration
def test_fr_025_merge_reassigns_faces(db_path: Path, tmp_path: Path) -> None:
    """merge_persons: all faces of source reassigned to target; source deleted."""
    image_id = _add_image(db_path, tmp_path)
    source_id = _add_person(db_path, "Source")
    target_id = _add_person(db_path, "Target")
    _add_face_for_person(db_path, source_id, "face-001", image_id)
    _add_face_for_person(db_path, source_id, "face-002", image_id)

    result = merge_persons(db_path, source_id=source_id, target_id=target_id)

    assert isinstance(result, PersonMergeResult)
    assert result.reassigned_count == 2
    assert result.deleted_person_id == source_id

    # source gone
    with sqlite3.connect(db_path) as conn:
        row = conn.execute("SELECT 1 FROM persons WHERE person_id = ?", (source_id,)).fetchone()
    assert row is None

    # faces now owned by target
    with sqlite3.connect(db_path) as conn:
        count = conn.execute(
            "SELECT COUNT(*) FROM faces WHERE person_id = ?", (target_id,)
        ).fetchone()[0]
    assert count == 2


@pytest.mark.fr
@pytest.mark.integration
def test_fr_025_merge_nonexistent_raises(db_path: Path) -> None:
    pid = _add_person(db_path, "Alice")
    with pytest.raises(ValueError, match="not found"):
        merge_persons(db_path, source_id="bad-id", target_id=pid)


# ---------------------------------------------------------------------------
# delete_person (FR-028)
# ---------------------------------------------------------------------------


@pytest.mark.fr
@pytest.mark.integration
def test_fr_028_delete_person_with_embeddings(db_path: Path, tmp_path: Path) -> None:
    """delete_person(delete_embeddings=True) removes person + all face rows."""
    image_id = _add_image(db_path, tmp_path)
    pid = _add_person(db_path, "ToDelete")
    _add_face_for_person(db_path, pid, "face-del-1", image_id)
    _add_face_for_person(db_path, pid, "face-del-2", image_id)

    delete_person(db_path, pid, delete_embeddings=True)

    with sqlite3.connect(db_path) as conn:
        p_row = conn.execute("SELECT 1 FROM persons WHERE person_id = ?", (pid,)).fetchone()
        f_count = conn.execute("SELECT COUNT(*) FROM faces WHERE person_id = ?", (pid,)).fetchone()[
            0
        ]
        total_faces = conn.execute("SELECT COUNT(*) FROM faces").fetchone()[0]
    assert p_row is None
    assert f_count == 0
    assert total_faces == 0  # face rows deleted


@pytest.mark.fr
@pytest.mark.integration
def test_fr_028_delete_person_without_embeddings(db_path: Path, tmp_path: Path) -> None:
    """delete_person(delete_embeddings=False) removes person, nullifies face person_id."""
    image_id = _add_image(db_path, tmp_path)
    pid = _add_person(db_path, "ToUnlink")
    _add_face_for_person(db_path, pid, "face-unlink-1", image_id)

    delete_person(db_path, pid, delete_embeddings=False)

    with sqlite3.connect(db_path) as conn:
        p_row = conn.execute("SELECT 1 FROM persons WHERE person_id = ?", (pid,)).fetchone()
        face_person = conn.execute(
            "SELECT person_id FROM faces WHERE face_id = 'face-unlink-1'"
        ).fetchone()
    assert p_row is None
    assert face_person is not None
    assert face_person[0] is None  # unlinked but face row preserved


@pytest.mark.fr
@pytest.mark.integration
def test_fr_028_delete_nonexistent_raises(db_path: Path) -> None:
    with pytest.raises(ValueError, match="not found"):
        delete_person(db_path, "bad-id", delete_embeddings=True)
