"""Integration tests for FR-023: Schema v2 with faces and persons tables."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from rapidcull.models import FaceDetectionResult, FaceRecord, PersonRecord
from rapidcull.schema import (
    CURRENT_SCHEMA_VERSION,
    SchemaVersionMismatchError,
    create_or_validate_schema,
)


@pytest.mark.fr
@pytest.mark.integration
def test_fr_023_schema_version_is_2() -> None:
    """Schema version must be 2 to include faces and persons tables."""
    assert CURRENT_SCHEMA_VERSION == 2


@pytest.mark.fr
@pytest.mark.integration
def test_fr_023_schema_creates_persons_table(tmp_path: Path) -> None:
    """Schema init creates persons table with expected columns."""
    db_path = tmp_path / "test.db"
    create_or_validate_schema(db_path)

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='persons'")
        assert cursor.fetchone() is not None, "persons table not created"

        cursor.execute("PRAGMA table_info(persons)")
        columns = {row[1] for row in cursor.fetchall()}
        assert "person_id" in columns
        assert "name" in columns
        assert "created_at" in columns


@pytest.mark.fr
@pytest.mark.integration
def test_fr_023_schema_creates_faces_table(tmp_path: Path) -> None:
    """Schema init creates faces table with expected columns."""
    db_path = tmp_path / "test.db"
    create_or_validate_schema(db_path)

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='faces'")
        assert cursor.fetchone() is not None, "faces table not created"

        cursor.execute("PRAGMA table_info(faces)")
        columns = {row[1] for row in cursor.fetchall()}
        assert "face_id" in columns
        assert "image_id" in columns
        assert "person_id" in columns
        assert "embedding" in columns
        assert "bbox_x" in columns
        assert "bbox_y" in columns
        assert "bbox_w" in columns
        assert "bbox_h" in columns
        assert "detection_score" in columns


@pytest.mark.fr
@pytest.mark.integration
def test_fr_023_schema_v1_db_raises_mismatch_error(tmp_path: Path) -> None:
    """Opening a v1 DB with v2 schema code raises SchemaVersionMismatchError."""
    db_path = tmp_path / "test.db"

    # Create a v1 DB manually
    with sqlite3.connect(db_path) as conn:
        conn.execute("CREATE TABLE schema_version (version INTEGER NOT NULL)")
        conn.execute("INSERT INTO schema_version (version) VALUES (1)")
        conn.execute("CREATE TABLE images (image_id TEXT PRIMARY KEY, path TEXT NOT NULL UNIQUE)")
        conn.commit()

    with pytest.raises(SchemaVersionMismatchError):
        create_or_validate_schema(db_path)


@pytest.mark.fr
@pytest.mark.integration
def test_fr_023_schema_idempotent(tmp_path: Path) -> None:
    """Calling create_or_validate_schema twice on same DB does not raise."""
    db_path = tmp_path / "test.db"
    create_or_validate_schema(db_path)
    create_or_validate_schema(db_path)  # Should not raise


@pytest.mark.fr
@pytest.mark.integration
def test_fr_023_face_record_model() -> None:
    """FaceRecord is a frozen dataclass with expected fields."""
    record = FaceRecord(
        face_id="face-001",
        image_id="img-001",
        person_id=None,
        embedding=b"\x00" * 2048,
        bbox_x=10,
        bbox_y=20,
        bbox_w=100,
        bbox_h=120,
        detection_score=0.98,
    )
    assert record.face_id == "face-001"
    assert record.person_id is None
    assert len(record.embedding) == 2048


@pytest.mark.fr
@pytest.mark.integration
def test_fr_023_person_record_model() -> None:
    """PersonRecord is a frozen dataclass with expected fields."""
    record = PersonRecord(
        person_id="person-001",
        name="Alice",
        created_at="2026-06-14T00:00:00Z",
    )
    assert record.person_id == "person-001"
    assert record.name == "Alice"


@pytest.mark.fr
@pytest.mark.integration
def test_fr_023_face_detection_result_model() -> None:
    """FaceDetectionResult has processed/skipped/failed accounting."""
    result = FaceDetectionResult(
        processed_count=5,
        skipped_count=2,
        failed_count=1,
        failed_items=[],
    )
    assert result.processed_count == 5
    assert result.skipped_count == 2
    assert result.failed_count == 1
