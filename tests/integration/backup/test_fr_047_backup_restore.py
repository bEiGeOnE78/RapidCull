"""Integration tests: FR-047 backup and restore of DB + JSON state."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from rapidcull.backup import backup, restore
from rapidcull.schema import create_or_validate_schema


def _make_db(db_path: Path) -> None:
    create_or_validate_schema(db_path)
    with sqlite3.connect(db_path) as conn:
        conn.execute("INSERT INTO images VALUES ('img1', '/photos/a.jpg')")


def _make_json(path: Path, data: dict) -> None:  # type: ignore[type-arg]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data))


@pytest.mark.fr
@pytest.mark.integration
def test_backup_creates_timestamped_directory(tmp_path: Path) -> None:
    db_path = tmp_path / "rapidcull.db"
    _make_db(db_path)
    backup_root = tmp_path / "backups"

    result = backup(db_path=db_path, galleries_root=None, backup_root=backup_root)

    assert Path(result.backup_path).exists()
    assert backup_root in Path(result.backup_path).parents


@pytest.mark.fr
@pytest.mark.integration
def test_backup_copies_db_file(tmp_path: Path) -> None:
    db_path = tmp_path / "rapidcull.db"
    _make_db(db_path)
    backup_root = tmp_path / "backups"

    result = backup(db_path=db_path, galleries_root=None, backup_root=backup_root)

    backup_dir = Path(result.backup_path)
    assert (backup_dir / db_path.name).exists()
    assert result.files_backed_up >= 1


@pytest.mark.fr
@pytest.mark.integration
def test_backup_includes_gallery_json(tmp_path: Path) -> None:
    db_path = tmp_path / "rapidcull.db"
    _make_db(db_path)
    galleries_root = tmp_path / "galleries"
    gallery_a = galleries_root / "album_a"
    _make_json(gallery_a / "metadata.json", {"assets": []})
    backup_root = tmp_path / "backups"

    result = backup(db_path=db_path, galleries_root=galleries_root, backup_root=backup_root)

    assert result.files_backed_up >= 2
    assert result.total_bytes > 0


@pytest.mark.fr
@pytest.mark.integration
def test_backup_result_has_timestamp(tmp_path: Path) -> None:
    db_path = tmp_path / "rapidcull.db"
    _make_db(db_path)

    result = backup(db_path=db_path, galleries_root=None, backup_root=tmp_path / "backups")

    assert result.created_at != ""


@pytest.mark.fr
@pytest.mark.integration
def test_restore_requires_confirmed(tmp_path: Path) -> None:
    db_path = tmp_path / "rapidcull.db"
    _make_db(db_path)
    backup_root = tmp_path / "backups"
    result = backup(db_path=db_path, galleries_root=None, backup_root=backup_root)

    with pytest.raises(RuntimeError, match="confirmed=True"):
        restore(
            backup_path=Path(result.backup_path),
            db_path=db_path,
            galleries_root=None,
            confirmed=False,
        )


@pytest.mark.fr
@pytest.mark.integration
def test_restore_replaces_db(tmp_path: Path) -> None:
    db_path = tmp_path / "rapidcull.db"
    _make_db(db_path)
    backup_root = tmp_path / "backups"
    result = backup(db_path=db_path, galleries_root=None, backup_root=backup_root)

    db_path.write_bytes(b"corrupted")

    restore_result = restore(
        backup_path=Path(result.backup_path),
        db_path=db_path,
        galleries_root=None,
        confirmed=True,
    )

    assert restore_result.success is True
    with sqlite3.connect(db_path) as conn:
        conn.execute("SELECT version FROM schema_version").fetchone()


@pytest.mark.fr
@pytest.mark.integration
def test_restore_nonexistent_backup_fails(tmp_path: Path) -> None:
    db_path = tmp_path / "rapidcull.db"
    _make_db(db_path)

    result = restore(
        backup_path=tmp_path / "no_such_backup",
        db_path=db_path,
        galleries_root=None,
        confirmed=True,
    )

    assert result.success is False
    assert result.reason != ""
