"""Backup and restore for DB and gallery JSON state (FR-047)."""

from __future__ import annotations

import shutil
from datetime import UTC, datetime
from pathlib import Path

from rapidcull.models import BackupResult, RestoreResult


def backup(
    db_path: Path,
    galleries_root: Path | None,
    backup_root: Path,
) -> BackupResult:
    """Copy DB and gallery JSON files to a timestamped backup directory."""
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    backup_dir = backup_root / f"rapidcull-backup-{timestamp}"
    backup_dir.mkdir(parents=True, exist_ok=True)

    created_at = datetime.now(UTC).isoformat()
    files_backed_up = 0
    total_bytes = 0

    if db_path.exists():
        dest = backup_dir / db_path.name
        shutil.copy2(db_path, dest)
        files_backed_up += 1
        total_bytes += dest.stat().st_size

    if galleries_root is not None and galleries_root.exists():
        for json_file in galleries_root.rglob("*.json"):
            rel = json_file.relative_to(galleries_root)
            dest = backup_dir / "galleries" / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(json_file, dest)
            files_backed_up += 1
            total_bytes += dest.stat().st_size

    return BackupResult(
        backup_path=str(backup_dir),
        files_backed_up=files_backed_up,
        total_bytes=total_bytes,
        created_at=created_at,
    )


def restore(
    backup_path: Path,
    db_path: Path,
    galleries_root: Path | None,
    *,
    confirmed: bool,
) -> RestoreResult:
    """Restore DB and gallery JSON from a backup directory. confirmed=True required."""
    if not confirmed:
        raise RuntimeError("restore requires confirmed=True")

    if not backup_path.exists():
        return RestoreResult(success=False, files_restored=0, reason="backup path not found")

    files_restored = 0

    backed_up_db = backup_path / db_path.name
    if backed_up_db.exists():
        db_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(backed_up_db, db_path)
        files_restored += 1

    galleries_backup = backup_path / "galleries"
    if galleries_root is not None and galleries_backup.exists():
        for json_file in galleries_backup.rglob("*.json"):
            rel = json_file.relative_to(galleries_backup)
            dest = galleries_root / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(json_file, dest)
            files_restored += 1

    return RestoreResult(success=True, files_restored=files_restored)
