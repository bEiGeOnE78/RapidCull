"""Consistency check and repair for DB/FS drift (FR-048)."""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from rapidcull.models import (
    ConsistencyIssue,
    ConsistencyReport,
    RepairItem,
    RepairResult,
)


def check_consistency(
    db_path: Path,
    trash_dir: Path | None,
) -> ConsistencyReport:
    """Detect DB/FS drift. Returns report with all issues found. Read-only."""
    checked_at = datetime.now(UTC).isoformat()
    issues: list[ConsistencyIssue] = []

    with sqlite3.connect(db_path) as conn:
        # Check images table: paths that no longer exist on disk
        for row in conn.execute("SELECT image_id, path FROM images").fetchall():
            image_id, path = row
            if not Path(path).exists():
                issues.append(
                    ConsistencyIssue(
                        kind="missing_from_fs",
                        item_id=image_id,
                        detail=f"path not found: {path}",
                    )
                )

        # Check trash table: entries whose file is not in trash_dir
        if trash_dir is not None:
            for row in conn.execute("SELECT image_id FROM trash").fetchall():
                image_id = row[0]
                if not (trash_dir / image_id).exists():
                    issues.append(
                        ConsistencyIssue(
                            kind="trash_orphan",
                            item_id=image_id,
                            detail=f"no file in trash_dir for {image_id}",
                        )
                    )

    return ConsistencyReport(issues=issues, checked_at=checked_at)


def repair_consistency(
    db_path: Path,
    report: ConsistencyReport,
    trash_dir: Path | None,
    *,
    confirmed: bool,
) -> RepairResult:
    """Fix issues from a ConsistencyReport. confirmed=True required."""
    if not confirmed:
        raise RuntimeError("repair_consistency requires confirmed=True")

    audit: list[RepairItem] = []
    fixed = 0
    skipped = 0
    failed = 0

    with sqlite3.connect(db_path) as conn:
        for issue in report.issues:
            try:
                if issue.kind == "missing_from_fs":
                    conn.execute("DELETE FROM cull_decisions WHERE image_id = ?", (issue.item_id,))
                    conn.execute("DELETE FROM faces WHERE image_id = ?", (issue.item_id,))
                    conn.execute("DELETE FROM images WHERE image_id = ?", (issue.item_id,))
                    audit.append(
                        RepairItem(
                            item_id=issue.item_id,
                            action="removed missing image from DB",
                            outcome="fixed",
                        )
                    )
                    fixed += 1
                elif issue.kind == "trash_orphan":
                    conn.execute("DELETE FROM trash WHERE image_id = ?", (issue.item_id,))
                    audit.append(
                        RepairItem(
                            item_id=issue.item_id,
                            action="removed orphaned trash entry",
                            outcome="fixed",
                        )
                    )
                    fixed += 1
                else:
                    audit.append(
                        RepairItem(
                            item_id=issue.item_id,
                            action="unknown issue kind",
                            outcome="skipped",
                        )
                    )
                    skipped += 1
            except sqlite3.Error as exc:
                audit.append(
                    RepairItem(
                        item_id=issue.item_id,
                        action=f"repair {issue.kind}",
                        outcome="failed",
                        reason=str(exc),
                    )
                )
                failed += 1

    return RepairResult(
        fixed_count=fixed,
        skipped_count=skipped,
        failed_count=failed,
        audit=audit,
    )
