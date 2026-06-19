"""Integration tests: FR-048 consistency check and repair."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from rapidcull.consistency import check_consistency, repair_consistency
from rapidcull.schema import create_or_validate_schema


def _add_image(db_path: Path, image_id: str, path: str) -> None:
    with sqlite3.connect(db_path) as conn:
        conn.execute("INSERT INTO images VALUES (?, ?)", (image_id, path))


def _add_trash(db_path: Path, image_id: str, original_path: str) -> None:
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "INSERT INTO trash (image_id, original_path, trashed_at) VALUES (?, ?, '2026-01-01')",
            (image_id, original_path),
        )


@pytest.mark.fr
@pytest.mark.integration
def test_check_clean_db_has_no_issues(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    create_or_validate_schema(db_path)
    photo = tmp_path / "a.jpg"
    photo.write_bytes(b"img")
    _add_image(db_path, "img1", str(photo))

    report = check_consistency(db_path, trash_dir=None)

    assert report.issues == []
    assert report.checked_at != ""


@pytest.mark.fr
@pytest.mark.integration
def test_check_detects_missing_from_fs(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    create_or_validate_schema(db_path)
    _add_image(db_path, "img1", str(tmp_path / "gone.jpg"))  # file doesn't exist

    report = check_consistency(db_path, trash_dir=None)

    assert len(report.issues) == 1
    assert report.issues[0].kind == "missing_from_fs"
    assert report.issues[0].item_id == "img1"


@pytest.mark.fr
@pytest.mark.integration
def test_check_detects_trash_orphan(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    trash_dir = tmp_path / ".trash"
    trash_dir.mkdir()
    create_or_validate_schema(db_path)
    # Add trash entry but no file in trash_dir
    _add_trash(db_path, "img1", "/original/path.jpg")

    report = check_consistency(db_path, trash_dir=trash_dir)

    assert any(i.kind == "trash_orphan" and i.item_id == "img1" for i in report.issues)


@pytest.mark.fr
@pytest.mark.integration
def test_check_no_trash_orphan_when_file_exists(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    trash_dir = tmp_path / ".trash"
    trash_dir.mkdir()
    create_or_validate_schema(db_path)
    (trash_dir / "img1").write_bytes(b"data")
    _add_trash(db_path, "img1", "/original/path.jpg")

    report = check_consistency(db_path, trash_dir=trash_dir)

    assert not any(i.kind == "trash_orphan" for i in report.issues)


@pytest.mark.fr
@pytest.mark.integration
def test_repair_requires_confirmed(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    create_or_validate_schema(db_path)
    _add_image(db_path, "img1", str(tmp_path / "gone.jpg"))
    report = check_consistency(db_path, trash_dir=None)

    with pytest.raises(RuntimeError, match="confirmed=True"):
        repair_consistency(db_path, report, trash_dir=None, confirmed=False)


@pytest.mark.fr
@pytest.mark.integration
def test_repair_removes_missing_from_fs(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    create_or_validate_schema(db_path)
    _add_image(db_path, "img1", str(tmp_path / "gone.jpg"))
    report = check_consistency(db_path, trash_dir=None)

    result = repair_consistency(db_path, report, trash_dir=None, confirmed=True)

    assert result.fixed_count == 1
    with sqlite3.connect(db_path) as conn:
        row = conn.execute("SELECT image_id FROM images WHERE image_id = 'img1'").fetchone()
    assert row is None


@pytest.mark.fr
@pytest.mark.integration
def test_repair_removes_trash_orphan(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    trash_dir = tmp_path / ".trash"
    trash_dir.mkdir()
    create_or_validate_schema(db_path)
    _add_trash(db_path, "img1", "/original/path.jpg")
    report = check_consistency(db_path, trash_dir=trash_dir)

    result = repair_consistency(db_path, report, trash_dir=trash_dir, confirmed=True)

    assert result.fixed_count >= 1
    with sqlite3.connect(db_path) as conn:
        row = conn.execute("SELECT image_id FROM trash WHERE image_id = 'img1'").fetchone()
    assert row is None


@pytest.mark.fr
@pytest.mark.integration
def test_repair_empty_report_does_nothing(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    create_or_validate_schema(db_path)
    report = check_consistency(db_path, trash_dir=None)

    result = repair_consistency(db_path, report, trash_dir=None, confirmed=True)

    assert result.fixed_count == 0
    assert result.failed_count == 0
