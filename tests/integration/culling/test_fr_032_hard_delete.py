"""Integration tests: FR-032 hard delete with audit trail."""

import sqlite3
from pathlib import Path

import pytest

from rapidcull.culling import hard_delete, move_to_trash, set_decision
from rapidcull.schema import create_or_validate_schema


def _add_image(db_path: Path, image_id: str, path: str) -> None:
    with sqlite3.connect(db_path) as conn:
        conn.execute("INSERT INTO images VALUES (?, ?)", (image_id, path))


def _make_file(path: Path, content: bytes = b"pixels") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


def _setup_trashed(db_path: Path, trash_dir: Path, tmp_path: Path, image_id: str) -> Path:
    photos = tmp_path / "photos"
    photo = photos / f"{image_id}.jpg"
    _make_file(photo, b"x" * 42)
    _add_image(db_path, image_id, str(photo))
    set_decision(db_path, image_id, "reject")
    move_to_trash(db_path, [image_id], trash_dir)
    return photo


def test_hard_delete_confirmed_false_raises(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    trash_dir = tmp_path / ".trash"
    create_or_validate_schema(db_path)

    with pytest.raises(RuntimeError, match="confirmed=True"):
        hard_delete(db_path, ["img1"], trash_dir, confirmed=False)


def test_hard_delete_confirmed_false_no_file_mutation(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    trash_dir = tmp_path / ".trash"
    create_or_validate_schema(db_path)
    _setup_trashed(db_path, trash_dir, tmp_path, "img1")
    assert (trash_dir / "img1").exists()

    with pytest.raises(RuntimeError):
        hard_delete(db_path, ["img1"], trash_dir, confirmed=False)

    assert (trash_dir / "img1").exists()


def test_hard_delete_removes_file_and_trash_row(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    trash_dir = tmp_path / ".trash"
    create_or_validate_schema(db_path)
    _setup_trashed(db_path, trash_dir, tmp_path, "img1")

    result = hard_delete(db_path, ["img1"], trash_dir, confirmed=True)

    assert result.deleted_count == 1
    assert result.failed_count == 0
    assert not (trash_dir / "img1").exists()
    with sqlite3.connect(db_path) as conn:
        row = conn.execute("SELECT image_id FROM trash WHERE image_id = 'img1'").fetchone()
    assert row is None


def test_hard_delete_audit_entry_has_path_and_size(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    trash_dir = tmp_path / ".trash"
    create_or_validate_schema(db_path)
    _setup_trashed(db_path, trash_dir, tmp_path, "img1")

    result = hard_delete(db_path, ["img1"], trash_dir, confirmed=True)

    assert len(result.audit) == 1
    entry = result.audit[0]
    assert entry.outcome == "deleted"
    assert entry.size_bytes == 42
    assert entry.original_path != ""
    assert entry.deleted_at != ""


def test_hard_delete_continue_on_error_missing_trash_file(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    trash_dir = tmp_path / ".trash"
    create_or_validate_schema(db_path)
    _setup_trashed(db_path, trash_dir, tmp_path, "img1")
    (trash_dir / "img1").unlink()  # simulate missing file

    result = hard_delete(db_path, ["img1"], trash_dir, confirmed=True)

    # file gone but DB row still cleaned; counts as deleted
    assert result.deleted_count == 1
    assert result.failed_count == 0


def test_hard_delete_unknown_image_id_fails(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    trash_dir = tmp_path / ".trash"
    create_or_validate_schema(db_path)

    result = hard_delete(db_path, ["no-such-id"], trash_dir, confirmed=True)

    assert result.deleted_count == 0
    assert result.failed_count == 1
    assert result.audit[0].outcome == "failed"
    assert "not found" in result.audit[0].reason
