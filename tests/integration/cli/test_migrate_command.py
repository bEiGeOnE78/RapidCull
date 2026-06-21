"""Integration tests: rapidcull migrate status / run CLI subcommands."""
from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from rapidcull.cli import cli
from rapidcull.schema import CURRENT_SCHEMA_VERSION, get_schema_version


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def fresh_db(tmp_path: Path) -> Path:
    return tmp_path / "rapidcull.db"


def test_migrate_status_fresh_db_shows_none_current(
    runner: CliRunner, fresh_db: Path
) -> None:
    """status on a non-existent DB prints current: none and target: <version>."""
    result = runner.invoke(cli, ["migrate", "status", "--db-path", str(fresh_db)])
    assert result.exit_code == 0, result.output
    assert f"target: {CURRENT_SCHEMA_VERSION}" in result.output
    assert "current: none" in result.output
    assert f"pending: none→{CURRENT_SCHEMA_VERSION}" in result.output


def test_migrate_run_creates_schema(runner: CliRunner, fresh_db: Path) -> None:
    """run on a fresh DB should create schema at CURRENT_SCHEMA_VERSION."""
    result = runner.invoke(cli, ["migrate", "run", "--db-path", str(fresh_db)])
    assert result.exit_code == 0, result.output
    assert get_schema_version(fresh_db) == CURRENT_SCHEMA_VERSION
    assert f"after: {CURRENT_SCHEMA_VERSION}" in result.output


def test_migrate_status_after_run_shows_up_to_date(
    runner: CliRunner, fresh_db: Path
) -> None:
    """After run, status should show 'up to date'."""
    runner.invoke(cli, ["migrate", "run", "--db-path", str(fresh_db)])
    result = runner.invoke(cli, ["migrate", "status", "--db-path", str(fresh_db)])
    assert result.exit_code == 0, result.output
    assert "up to date" in result.output


def test_migrate_run_idempotent(runner: CliRunner, fresh_db: Path) -> None:
    """Running migrate run twice must not error."""
    runner.invoke(cli, ["migrate", "run", "--db-path", str(fresh_db)])
    result = runner.invoke(cli, ["migrate", "run", "--db-path", str(fresh_db)])
    assert result.exit_code == 0, result.output
    assert "up to date (no migration needed)" in result.output


def test_migrate_status_no_db_path_no_env_errors(runner: CliRunner) -> None:
    """status without --db-path and no env var must exit non-zero."""
    env = {}  # empty env — no RAPIDCULL_DB_PATH
    result = runner.invoke(cli, ["migrate", "status"], env=env, catch_exceptions=False)
    assert result.exit_code != 0
