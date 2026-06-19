"""Cull decision persistence: picks, rejects, trash, and hard delete."""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from rapidcull.models import CullDecision, CullResult


def set_decision(
    db_path: Path,
    image_id: str,
    decision: Literal["pick", "reject"],
) -> CullResult:
    """Persist a pick or reject for image_id. Upserts on conflict."""
    decided_at = datetime.now(UTC).isoformat()
    with sqlite3.connect(db_path) as conn:
        row = conn.execute("SELECT image_id FROM images WHERE image_id = ?", (image_id,)).fetchone()
        if row is None:
            raise ValueError(f"image_id not found: {image_id}")
        conn.execute(
            "INSERT INTO cull_decisions (image_id, decision, decided_at) VALUES (?, ?, ?)"
            " ON CONFLICT(image_id) DO UPDATE SET decision = excluded.decision,"
            " decided_at = excluded.decided_at",
            (image_id, decision, decided_at),
        )
    return CullResult(image_id=image_id, success=True)


def get_decision(db_path: Path, image_id: str) -> CullDecision | None:
    """Return stored decision for image_id, or None if not set."""
    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            "SELECT image_id, decision, decided_at FROM cull_decisions WHERE image_id = ?",
            (image_id,),
        ).fetchone()
    if row is None:
        return None
    return CullDecision(image_id=row[0], decision=row[1], decided_at=row[2])


def list_decisions(
    db_path: Path,
    filter: Literal["pick", "reject"] | None = None,
) -> list[CullDecision]:
    """Return all decisions, optionally filtered by pick or reject."""
    with sqlite3.connect(db_path) as conn:
        if filter is None:
            rows = conn.execute(
                "SELECT image_id, decision, decided_at FROM cull_decisions" " ORDER BY decided_at"
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT image_id, decision, decided_at FROM cull_decisions"
                " WHERE decision = ? ORDER BY decided_at",
                (filter,),
            ).fetchall()
    return [CullDecision(image_id=r[0], decision=r[1], decided_at=r[2]) for r in rows]


def undo_decision(db_path: Path, image_id: str) -> CullResult:
    """Remove stored decision for image_id."""
    with sqlite3.connect(db_path) as conn:
        conn.execute("DELETE FROM cull_decisions WHERE image_id = ?", (image_id,))
    return CullResult(image_id=image_id, success=True)
