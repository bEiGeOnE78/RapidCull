"""Integration tests: FR-031 trash-first soft delete."""

import sqlite3
from pathlib import Path

from rapidcull.culling import (
    list_trash,
    move_to_trash,
    preview_trash,
    restore_from_trash,
    set_decision,
)
from rapidcull.schema import create_or_validate_schema


def _add_image(db_path: Path, image_id: str, path: str) -> None:
    with sqlite3.connect(db_path) as conn:
        conn.execute("INSERT INTO images VALUES (?, ?, ?)", (image_id, path, None))


def _make_file(path: Path, content: bytes = b"x") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


def test_preview_trash_lists_rejected_images(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    photos = tmp_path / "photos"
    create_or_validate_schema(db_path)
    _make_file(photos / "a.jpg", b"imgdata")
    _make_file(photos / "b.jpg", b"imgdata")
    _add_image(db_path, "img1", str(photos / "a.jpg"))
    _add_image(db_path, "img2", str(photos / "b.jpg"))
    set_decision(db_path, "img1", "reject")
    set_decision(db_path, "img2", "pick")

    preview = preview_trash(db_path)

    assert len(preview.items) == 1
    assert preview.items[0].image_id == "img1"


def test_preview_trash_is_readonly(tmp_path: Path) -> None:
    """preview_trash must not move or delete any files."""
    db_path = tmp_path / "test.db"
    photos = tmp_path / "photos"
    create_or_validate_schema(db_path)
    _make_file(photos / "a.jpg")
    _add_image(db_path, "img1", str(photos / "a.jpg"))
    set_decision(db_path, "img1", "reject")

    preview_trash(db_path)

    assert (photos / "a.jpg").exists()


def test_move_to_trash_moves_file_and_removes_from_images(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    photos = tmp_path / "photos"
    trash_dir = tmp_path / ".trash"
    create_or_validate_schema(db_path)
    _make_file(photos / "a.jpg", b"pixels")
    _add_image(db_path, "img1", str(photos / "a.jpg"))
    set_decision(db_path, "img1", "reject")

    result = move_to_trash(db_path, ["img1"], trash_dir)

    assert result.moved_count == 1
    assert result.failed_count == 0
    assert not (photos / "a.jpg").exists()
    assert (trash_dir / "img1").exists()
    with sqlite3.connect(db_path) as conn:
        row = conn.execute("SELECT image_id FROM images WHERE image_id = 'img1'").fetchone()
    assert row is None


def test_move_to_trash_continue_on_error_missing_file(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    trash_dir = tmp_path / ".trash"
    create_or_validate_schema(db_path)
    _add_image(db_path, "img1", str(tmp_path / "photos" / "gone.jpg"))
    set_decision(db_path, "img1", "reject")

    result = move_to_trash(db_path, ["img1"], trash_dir)

    # file didn't exist but DB row still removed
    assert result.moved_count == 1
    assert result.failed_count == 0


def test_move_to_trash_unknown_image_id_fails(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    trash_dir = tmp_path / ".trash"
    create_or_validate_schema(db_path)

    result = move_to_trash(db_path, ["no-such-id"], trash_dir)

    assert result.moved_count == 0
    assert result.failed_count == 1
    assert "not found" in result.failed_items[0].reason


def test_list_trash_shows_trashed_items(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    photos = tmp_path / "photos"
    trash_dir = tmp_path / ".trash"
    create_or_validate_schema(db_path)
    _make_file(photos / "a.jpg")
    _add_image(db_path, "img1", str(photos / "a.jpg"))
    set_decision(db_path, "img1", "reject")
    move_to_trash(db_path, ["img1"], trash_dir)

    entries = list_trash(db_path)

    assert len(entries) == 1
    assert entries[0].image_id == "img1"


def test_restore_from_trash_moves_file_back(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    photos = tmp_path / "photos"
    trash_dir = tmp_path / ".trash"
    create_or_validate_schema(db_path)
    _make_file(photos / "a.jpg", b"pixels")
    _add_image(db_path, "img1", str(photos / "a.jpg"))
    set_decision(db_path, "img1", "reject")
    move_to_trash(db_path, ["img1"], trash_dir)

    result = restore_from_trash(db_path, "img1", trash_dir)

    assert result.success is True
    assert (photos / "a.jpg").exists()
    with sqlite3.connect(db_path) as conn:
        row = conn.execute("SELECT image_id FROM images WHERE image_id = 'img1'").fetchone()
    assert row is not None
    assert len(list_trash(db_path)) == 0
