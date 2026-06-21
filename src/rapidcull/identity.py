from __future__ import annotations

import hashlib
import json
import sqlite3
import uuid
from pathlib import Path
from typing import Any

from .models import ImageRecord
from .schema import create_or_validate_schema


def create_image_record(db_path: Path, file_path: Path) -> ImageRecord:
    create_or_validate_schema(db_path)
    normalized_path = str(file_path.resolve())

    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT image_id, path FROM images WHERE path = ?", (normalized_path,))
        row = cursor.fetchone()
        if row is not None:
            return ImageRecord(image_id=str(row[0]), path=str(row[1]))

        image_id = _generate_image_id(normalized_path)
        cursor.execute(
            "INSERT INTO images (image_id, path) VALUES (?, ?)",
            (image_id, normalized_path),
        )
        connection.commit()
        return ImageRecord(image_id=image_id, path=normalized_path)


def fetch_image_record(db_path: Path, file_path: Path) -> ImageRecord | None:
    create_or_validate_schema(db_path)
    normalized_path = str(file_path.resolve())

    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT image_id, path FROM images WHERE path = ?", (normalized_path,))
        row = cursor.fetchone()
        if row is None:
            return None
        return ImageRecord(image_id=str(row[0]), path=str(row[1]))


def update_thumbnail_path(db_path: Path, file_path: Path, thumbnail_path: Path) -> None:
    normalized_path = str(file_path.resolve())
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            "UPDATE images SET thumbnail_path = ? WHERE path = ?",
            (str(thumbnail_path.resolve()), normalized_path),
        )
        connection.commit()


def update_display_path(db_path: Path, file_path: Path, display_path: Path) -> None:
    normalized_path = str(file_path.resolve())
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            "UPDATE images SET display_path = ? WHERE path = ?",
            (str(display_path.resolve()), normalized_path),
        )
        connection.commit()


def update_full_path(db_path: Path, file_path: Path, full_path: Path) -> None:
    normalized_path = str(file_path.resolve())
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            "UPDATE images SET full_path = ? WHERE path = ?",
            (str(full_path.resolve()), normalized_path),
        )
        connection.commit()


def update_metadata(db_path: Path, file_path: Path, metadata: dict[str, Any]) -> None:
    normalized_path = str(file_path.resolve())
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            "UPDATE images SET metadata = ? WHERE path = ?",
            (json.dumps(metadata), normalized_path),
        )
        connection.commit()


def get_paths_with_missing_proxies(db_path: Path) -> list[Path]:
    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT path FROM images WHERE thumbnail_path IS NULL OR display_path IS NULL"
        )
        return [Path(row[0]) for row in cursor.fetchall()]


def _generate_image_id(path: str) -> str:
    stable_hash = hashlib.sha1(path.encode("utf-8")).hexdigest()[:16]
    namespace = uuid.UUID("12345678-1234-5678-1234-567812345678")
    generated = uuid.uuid5(namespace, stable_hash)
    return str(generated)
