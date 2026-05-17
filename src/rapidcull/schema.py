from __future__ import annotations

import sqlite3
from pathlib import Path

CURRENT_SCHEMA_VERSION = 1


class SchemaVersionMismatchError(RuntimeError):
    """Raised when the on-disk schema version doesn't match expected version."""


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
            connection.commit()
            return

        existing_version = int(row[0])
        if existing_version != CURRENT_SCHEMA_VERSION:
            raise SchemaVersionMismatchError(
                "Schema version mismatch detected. Please run migration tooling. "
                f"Expected {CURRENT_SCHEMA_VERSION}, found {existing_version}."
            )

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS images (
              image_id TEXT PRIMARY KEY,
              path TEXT NOT NULL UNIQUE
            )
            """)
        connection.commit()
