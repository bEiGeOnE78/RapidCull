"""Integration tests: CLI backup, restore, and check commands."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest
from click.testing import CliRunner

from rapidcull.cli import cli
from rapidcull.schema import create_or_validate_schema


def _make_db(db_path: Path) -> None:
    create_or_validate_schema(db_path)
    with sqlite3.connect(db_path) as conn:
        conn.execute("INSERT INTO images (image_id, path, thumbnail_path) VALUES ('img1', '/photos/a.jpg', NULL)")


@pytest.mark.fr
@pytest.mark.integration
def test_cli_backup_exits_zero(tmp_path: Path) -> None:
    db_path = tmp_path / "rapidcull.db"
    _make_db(db_path)
    backup_root = tmp_path / "backups"
    runner = CliRunner()

    result = runner.invoke(cli, ["backup", "--db", str(db_path), "--backup-root", str(backup_root)])

    assert result.exit_code == 0, result.output
    assert "Backed up" in result.output


@pytest.mark.fr
@pytest.mark.integration
def test_cli_backup_creates_backup_dir(tmp_path: Path) -> None:
    db_path = tmp_path / "rapidcull.db"
    _make_db(db_path)
    backup_root = tmp_path / "backups"
    runner = CliRunner()

    runner.invoke(cli, ["backup", "--db", str(db_path), "--backup-root", str(backup_root)])

    assert backup_root.exists()
    assert any(backup_root.iterdir())


@pytest.mark.fr
@pytest.mark.integration
def test_cli_restore_requires_confirmed_flag(tmp_path: Path) -> None:
    db_path = tmp_path / "rapidcull.db"
    _make_db(db_path)
    backup_root = tmp_path / "backups"
    runner = CliRunner()
    runner.invoke(cli, ["backup", "--db", str(db_path), "--backup-root", str(backup_root)])
    backup_dirs = list(backup_root.iterdir())
    backup_dir = backup_dirs[0]

    result = runner.invoke(cli, ["restore", "--backup-path", str(backup_dir), "--db", str(db_path)])

    assert result.exit_code != 0 or "confirmed" in result.output.lower()


@pytest.mark.fr
@pytest.mark.integration
def test_cli_restore_with_confirmed_succeeds(tmp_path: Path) -> None:
    db_path = tmp_path / "rapidcull.db"
    _make_db(db_path)
    backup_root = tmp_path / "backups"
    runner = CliRunner()
    runner.invoke(cli, ["backup", "--db", str(db_path), "--backup-root", str(backup_root)])
    backup_dirs = list(backup_root.iterdir())
    backup_dir = backup_dirs[0]
    db_path.write_bytes(b"corrupted")

    result = runner.invoke(
        cli,
        ["restore", "--backup-path", str(backup_dir), "--db", str(db_path), "--confirmed"],
    )

    assert result.exit_code == 0, result.output
    assert "Restored" in result.output


@pytest.mark.fr
@pytest.mark.integration
def test_cli_check_clean_db(tmp_path: Path) -> None:
    db_path = tmp_path / "rapidcull.db"
    create_or_validate_schema(db_path)
    runner = CliRunner()

    result = runner.invoke(cli, ["check", "--db", str(db_path)])

    assert result.exit_code == 0, result.output
    assert "issues" in result.output.lower() or "0" in result.output


@pytest.mark.fr
@pytest.mark.integration
def test_cli_check_reports_missing_files(tmp_path: Path) -> None:
    db_path = tmp_path / "rapidcull.db"
    create_or_validate_schema(db_path)
    with sqlite3.connect(db_path) as conn:
        conn.execute("INSERT INTO images (image_id, path, thumbnail_path) VALUES ('img1', '/nonexistent/gone.jpg', NULL)")
    runner = CliRunner()

    result = runner.invoke(cli, ["check", "--db", str(db_path)])

    assert result.exit_code == 0, result.output
    assert "missing_from_fs" in result.output or "1" in result.output
