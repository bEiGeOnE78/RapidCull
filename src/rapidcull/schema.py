from __future__ import annotations

import sqlite3
from pathlib import Path

from rapidcull.models import MigrationStep

CURRENT_SCHEMA_VERSION = 6

MIGRATION_PATH = [
    MigrationStep(from_version=1, to_version=2, description="Add faces and persons tables"),
    MigrationStep(from_version=2, to_version=3, description="Add cull_decisions and trash tables"),
    MigrationStep(from_version=3, to_version=4, description="Add thumbnail_path to images"),
    MigrationStep(from_version=4, to_version=5, description="Add display_path and metadata to images"),
    MigrationStep(from_version=5, to_version=6, description="Add full_path to images"),
]


class SchemaVersionMismatchError(RuntimeError):
    """Raised when the on-disk schema version doesn't match expected version."""


def _apply_v2_tables(cursor: sqlite3.Cursor) -> None:
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS persons (
          person_id TEXT PRIMARY KEY,
          name TEXT NOT NULL,
          created_at TEXT NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS faces (
          face_id TEXT PRIMARY KEY,
          image_id TEXT NOT NULL REFERENCES images(image_id),
          person_id TEXT REFERENCES persons(person_id),
          embedding BLOB NOT NULL,
          bbox_x INTEGER NOT NULL,
          bbox_y INTEGER NOT NULL,
          bbox_w INTEGER NOT NULL,
          bbox_h INTEGER NOT NULL,
          detection_score REAL NOT NULL
        )
    """)


def _apply_v3_tables(cursor: sqlite3.Cursor) -> None:
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cull_decisions (
          image_id TEXT PRIMARY KEY REFERENCES images(image_id),
          decision TEXT NOT NULL CHECK(decision IN ('pick', 'reject')),
          decided_at TEXT NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trash (
          image_id TEXT PRIMARY KEY REFERENCES images(image_id),
          original_path TEXT NOT NULL,
          trashed_at TEXT NOT NULL
        )
    """)


def _migrate_v2_to_v3(cursor: sqlite3.Cursor) -> None:
    _apply_v3_tables(cursor)
    cursor.execute("UPDATE schema_version SET version = 3")


def _migrate_v3_to_v4(cursor: sqlite3.Cursor) -> None:
    cursor.execute("ALTER TABLE images ADD COLUMN thumbnail_path TEXT")
    cursor.execute("UPDATE schema_version SET version = 4")


def _migrate_v4_to_v5(cursor: sqlite3.Cursor) -> None:
    cursor.execute("ALTER TABLE images ADD COLUMN display_path TEXT")
    cursor.execute("ALTER TABLE images ADD COLUMN metadata TEXT")
    cursor.execute("UPDATE schema_version SET version = 5")


def _migrate_v5_to_v6(cursor: sqlite3.Cursor) -> None:
    cursor.execute("ALTER TABLE images ADD COLUMN full_path TEXT")
    cursor.execute("UPDATE schema_version SET version = 6")


def get_schema_version(db_path: Path) -> int | None:
    """Return current schema version from DB, or None if DB doesn't exist/has no version table."""
    if not db_path.exists():
        return None
    with sqlite3.connect(db_path) as conn:
        try:
            row = conn.execute("SELECT version FROM schema_version LIMIT 1").fetchone()
            return int(row[0]) if row else None
        except sqlite3.OperationalError:
            return None


def create_or_validate_schema(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schema_version (
              version INTEGER NOT NULL
            )
            """)

        cursor.execute("SELECT version FROM schema_version LIMIT 1")
        row = cursor.fetchone()

        if row is None:
            cursor.execute(
                "INSERT INTO schema_version (version) VALUES (?)", (CURRENT_SCHEMA_VERSION,)
            )
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS images (
                  image_id TEXT PRIMARY KEY,
                  path TEXT NOT NULL UNIQUE,
                  thumbnail_path TEXT,
                  display_path TEXT,
                  metadata TEXT,
                  full_path TEXT
                )
                """)
            _apply_v2_tables(cursor)
            _apply_v3_tables(cursor)
            connection.commit()
            return

        existing_version = int(row[0])

        if existing_version == 2:
            _migrate_v2_to_v3(cursor)
            connection.commit()
            existing_version = 3

        if existing_version == 3:
            _migrate_v3_to_v4(cursor)
            connection.commit()
            existing_version = 4

        if existing_version == 4:
            _migrate_v4_to_v5(cursor)
            connection.commit()
            existing_version = 5

        if existing_version == 5:
            _migrate_v5_to_v6(cursor)
            connection.commit()
            existing_version = 6

        if existing_version != CURRENT_SCHEMA_VERSION:
            raise SchemaVersionMismatchError(
                "Schema version mismatch detected. Please run migration tooling. "
                f"Expected {CURRENT_SCHEMA_VERSION}, found {existing_version}."
            )

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS images (
              image_id TEXT PRIMARY KEY,
              path TEXT NOT NULL UNIQUE,
              thumbnail_path TEXT,
              display_path TEXT,
              metadata TEXT,
              full_path TEXT
            )
            """)
        _apply_v2_tables(cursor)
        _apply_v3_tables(cursor)
        connection.commit()
