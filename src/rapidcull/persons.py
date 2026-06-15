from __future__ import annotations

import sqlite3
from pathlib import Path

from rapidcull.models import PersonMergeResult, PersonRecord


def list_persons(db_path: Path) -> list[PersonRecord]:
    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            "SELECT person_id, name, created_at FROM persons ORDER BY name"
        ).fetchall()
    return [PersonRecord(person_id=row[0], name=row[1], created_at=row[2]) for row in rows]


def rename_person(db_path: Path, person_id: str, new_name: str) -> PersonRecord:
    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            "SELECT person_id, created_at FROM persons WHERE person_id = ?", (person_id,)
        ).fetchone()
        if row is None:
            raise ValueError(f"Person '{person_id}' not found.")
        conn.execute("UPDATE persons SET name = ? WHERE person_id = ?", (new_name, person_id))
        conn.commit()
    return PersonRecord(person_id=person_id, name=new_name, created_at=row[1])


def merge_persons(db_path: Path, source_id: str, target_id: str) -> PersonMergeResult:
    with sqlite3.connect(db_path) as conn:
        src = conn.execute("SELECT 1 FROM persons WHERE person_id = ?", (source_id,)).fetchone()
        if src is None:
            raise ValueError(f"Person '{source_id}' not found.")
        tgt = conn.execute("SELECT 1 FROM persons WHERE person_id = ?", (target_id,)).fetchone()
        if tgt is None:
            raise ValueError(f"Person '{target_id}' not found.")

        count = conn.execute(
            "SELECT COUNT(*) FROM faces WHERE person_id = ?", (source_id,)
        ).fetchone()[0]
        conn.execute("UPDATE faces SET person_id = ? WHERE person_id = ?", (target_id, source_id))
        conn.execute("DELETE FROM persons WHERE person_id = ?", (source_id,))
        conn.commit()

    return PersonMergeResult(reassigned_count=count, deleted_person_id=source_id)


def delete_person(db_path: Path, person_id: str, delete_embeddings: bool) -> None:
    with sqlite3.connect(db_path) as conn:
        row = conn.execute("SELECT 1 FROM persons WHERE person_id = ?", (person_id,)).fetchone()
        if row is None:
            raise ValueError(f"Person '{person_id}' not found.")

        if delete_embeddings:
            conn.execute("DELETE FROM faces WHERE person_id = ?", (person_id,))
        else:
            conn.execute("UPDATE faces SET person_id = NULL WHERE person_id = ?", (person_id,))
        conn.execute("DELETE FROM persons WHERE person_id = ?", (person_id,))
        conn.commit()
