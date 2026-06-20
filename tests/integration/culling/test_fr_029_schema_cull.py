"""Integration tests: FR-029 schema v3 — cull_decisions and trash tables."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from rapidcull.schema import (
    CURRENT_SCHEMA_VERSION,
    create_or_validate_schema,
)


@pytest.mark.fr
@pytest.mark.integration
def test_schema_version_is_3(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    create_or_validate_schema(db_path)
    assert CURRENT_SCHEMA_VERSION == 4


@pytest.mark.fr
@pytest.mark.integration
def test_schema_creates_cull_decisions_table(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    create_or_validate_schema(db_path)
    conn = sqlite3.connect(db_path)
    cols = {row[1] for row in conn.execute("PRAGMA table_info(cull_decisions)")}
    conn.close()
    assert cols == {"image_id", "decision", "decided_at"}


@pytest.mark.fr
@pytest.mark.integration
def test_schema_creates_trash_table(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    create_or_validate_schema(db_path)
    conn = sqlite3.connect(db_path)
    cols = {row[1] for row in conn.execute("PRAGMA table_info(trash)")}
    conn.close()
    assert cols == {"image_id", "original_path", "trashed_at"}


@pytest.mark.fr
@pytest.mark.integration
def test_migration_v2_to_v3_preserves_existing_data(tmp_path: Path) -> None:
    """v2→v3 migration must not lose existing images rows."""
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE schema_version (version INTEGER NOT NULL)")
    conn.execute("INSERT INTO schema_version VALUES (2)")
    conn.execute("CREATE TABLE images (image_id TEXT PRIMARY KEY, path TEXT NOT NULL UNIQUE)")
    conn.execute(
        "CREATE TABLE persons "
        "(person_id TEXT PRIMARY KEY, name TEXT NOT NULL, created_at TEXT NOT NULL)"
    )
    conn.execute(
        "CREATE TABLE faces ("
        "face_id TEXT PRIMARY KEY, image_id TEXT NOT NULL REFERENCES images(image_id),"
        "person_id TEXT REFERENCES persons(person_id), embedding BLOB NOT NULL,"
        "bbox_x INTEGER NOT NULL, bbox_y INTEGER NOT NULL, bbox_w INTEGER NOT NULL,"
        "bbox_h INTEGER NOT NULL, detection_score REAL NOT NULL)"
    )
    conn.execute("INSERT INTO images VALUES ('img1', '/some/path.jpg')")
    conn.commit()
    conn.close()

    create_or_validate_schema(db_path)

    conn = sqlite3.connect(db_path)
    rows = list(conn.execute("SELECT image_id FROM images"))
    version = conn.execute("SELECT version FROM schema_version").fetchone()[0]
    conn.close()
    assert rows == [("img1",)]
    assert version == 4
