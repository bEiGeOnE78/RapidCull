"""Cull decision persistence: picks, rejects, trash, and hard delete."""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from rapidcull.models import (
    CullDecision,
    CullResult,
    HardDeleteAuditEntry,
    HardDeleteResult,
    TrashEntry,
    TrashFailedItem,
    TrashPreview,
    TrashResult,
)


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


def preview_trash(db_path: Path) -> TrashPreview:
    """Return all rejected images with sizes. Read-only — no mutation."""
    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            "SELECT cd.image_id, i.path FROM cull_decisions cd"
            " JOIN images i ON i.image_id = cd.image_id"
            " WHERE cd.decision = 'reject' ORDER BY i.path"
        ).fetchall()
    items = []
    total_bytes = 0
    for image_id, path in rows:
        p = Path(path)
        size = p.stat().st_size if p.exists() else 0
        items.append(TrashEntry(image_id=image_id, original_path=path, trashed_at=""))
        total_bytes += size
    return TrashPreview(items=items, total_size_bytes=total_bytes)


def move_to_trash(db_path: Path, image_ids: list[str], trash_dir: Path) -> TrashResult:
    """Move files for image_ids to trash_dir. Continue-on-error."""
    trash_dir.mkdir(parents=True, exist_ok=True)
    trashed_at = datetime.now(UTC).isoformat()
    moved = 0
    failed: list[TrashFailedItem] = []

    # Use plain sqlite3.connect (FK OFF by default) because the legacy trash and
    # cull_decisions tables use bare REFERENCES without ON DELETE CASCADE — enabling
    # FK globally would reject the DELETE FROM images while those child rows exist.
    # We explicitly delete gallery_memberships before images to achieve the same
    # effect as CASCADE for the new table added in v7.
    with sqlite3.connect(db_path) as conn:
        for image_id in image_ids:
            row = conn.execute("SELECT path FROM images WHERE image_id = ?", (image_id,)).fetchone()
            if row is None:
                failed.append(
                    TrashFailedItem(
                        image_id=image_id,
                        original_path="",
                        reason="image_id not found in images table",
                    )
                )
                continue
            original_path = row[0]
            src = Path(original_path)
            dest = trash_dir / image_id
            try:
                if src.exists():
                    src.rename(dest)
                conn.execute(
                    "INSERT INTO trash (image_id, original_path, trashed_at) VALUES (?, ?, ?)"
                    " ON CONFLICT(image_id) DO NOTHING",
                    (image_id, original_path, trashed_at),
                )
                # Explicitly remove all child rows before deleting from images.
                # gallery_memberships: the ON DELETE CASCADE would fire with FK ON,
                # but since we use FK OFF here we do it manually.
                conn.execute("DELETE FROM cull_decisions WHERE image_id = ?", (image_id,))
                conn.execute("DELETE FROM gallery_memberships WHERE image_id = ?", (image_id,))
                conn.execute("DELETE FROM images WHERE image_id = ?", (image_id,))
                moved += 1
            except OSError as exc:
                failed.append(
                    TrashFailedItem(
                        image_id=image_id,
                        original_path=original_path,
                        reason=str(exc),
                    )
                )

    return TrashResult(
        moved_count=moved,
        failed_count=len(failed),
        failed_items=failed,
    )


def list_trash(db_path: Path) -> list[TrashEntry]:
    """Return all items currently in trash."""
    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            "SELECT image_id, original_path, trashed_at FROM trash ORDER BY trashed_at"
        ).fetchall()
    return [TrashEntry(image_id=r[0], original_path=r[1], trashed_at=r[2]) for r in rows]


def restore_from_trash(db_path: Path, image_id: str, trash_dir: Path) -> CullResult:
    """Move file back from trash_dir to original path, re-insert into images."""
    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            "SELECT original_path FROM trash WHERE image_id = ?", (image_id,)
        ).fetchone()
        if row is None:
            return CullResult(image_id=image_id, success=False, reason="not in trash")
        original_path = row[0]
        src = trash_dir / image_id
        dest = Path(original_path)
        try:
            if src.exists():
                dest.parent.mkdir(parents=True, exist_ok=True)
                src.rename(dest)
            conn.execute(
                "INSERT INTO images (image_id, path) VALUES (?, ?)"
                " ON CONFLICT(image_id) DO NOTHING",
                (image_id, original_path),
            )
            conn.execute("DELETE FROM trash WHERE image_id = ?", (image_id,))
        except OSError as exc:
            return CullResult(image_id=image_id, success=False, reason=str(exc))
    return CullResult(image_id=image_id, success=True)


def hard_delete(
    db_path: Path,
    image_ids: list[str],
    trash_dir: Path,
    *,
    confirmed: bool,
) -> HardDeleteResult:
    """Permanently delete files from trash_dir. confirmed=True required (NFR-015)."""
    if not confirmed:
        raise RuntimeError("hard_delete requires confirmed=True")

    deleted = 0
    failed = 0
    audit: list[HardDeleteAuditEntry] = []
    deleted_at = datetime.now(UTC).isoformat()

    with sqlite3.connect(db_path) as conn:
        for image_id in image_ids:
            row = conn.execute(
                "SELECT original_path FROM trash WHERE image_id = ?", (image_id,)
            ).fetchone()
            if row is None:
                audit.append(
                    HardDeleteAuditEntry(
                        image_id=image_id,
                        original_path="",
                        deleted_at=deleted_at,
                        size_bytes=0,
                        outcome="failed",
                        reason="image_id not found in trash",
                    )
                )
                failed += 1
                continue
            original_path = row[0]
            dest = trash_dir / image_id
            size = dest.stat().st_size if dest.exists() else 0
            try:
                if dest.exists():
                    dest.unlink()
                conn.execute("DELETE FROM trash WHERE image_id = ?", (image_id,))
                audit.append(
                    HardDeleteAuditEntry(
                        image_id=image_id,
                        original_path=original_path,
                        deleted_at=deleted_at,
                        size_bytes=size,
                        outcome="deleted",
                    )
                )
                deleted += 1
            except OSError as exc:
                audit.append(
                    HardDeleteAuditEntry(
                        image_id=image_id,
                        original_path=original_path,
                        deleted_at=deleted_at,
                        size_bytes=size,
                        outcome="failed",
                        reason=str(exc),
                    )
                )
                failed += 1

    return HardDeleteResult(deleted_count=deleted, failed_count=failed, audit=audit)
