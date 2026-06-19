"""Integration tests: FR-049 schema migration path with explicit versions."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from rapidcull.models import MigrationStep
from rapidcull.schema import (
    CURRENT_SCHEMA_VERSION,
    MIGRATION_PATH,
    create_or_validate_schema,
    get_schema_version,
)


@pytest.mark.fr
@pytest.mark.integration
def test_migration_path_is_list_of_steps() -> None:
    assert isinstance(MIGRATION_PATH, list)
    assert all(isinstance(s, MigrationStep) for s in MIGRATION_PATH)


@pytest.mark.fr
@pytest.mark.integration
def test_migration_path_covers_versions_1_to_current() -> None:
    versions = {s.from_version for s in MIGRATION_PATH}
    assert 1 in versions
    assert 2 in versions


@pytest.mark.fr
@pytest.mark.integration
def test_migration_path_steps_have_descriptions() -> None:
    for step in MIGRATION_PATH:
        assert step.description != ""


@pytest.mark.fr
@pytest.mark.integration
def test_get_schema_version_returns_none_for_missing_db(tmp_path: Path) -> None:
    assert get_schema_version(tmp_path / "noexist.db") is None


@pytest.mark.fr
@pytest.mark.integration
def test_get_schema_version_returns_current_after_create(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    create_or_validate_schema(db_path)
    assert get_schema_version(db_path) == CURRENT_SCHEMA_VERSION


@pytest.mark.fr
@pytest.mark.integration
def test_get_schema_version_returns_version_for_old_db(tmp_path: Path) -> None:
    db_path = tmp_path / "old.db"
    with sqlite3.connect(db_path) as conn:
        conn.execute("CREATE TABLE schema_version (version INTEGER NOT NULL)")
        conn.execute("INSERT INTO schema_version VALUES (1)")
    assert get_schema_version(db_path) == 1
