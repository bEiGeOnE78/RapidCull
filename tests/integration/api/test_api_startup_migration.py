"""Integration test: API startup triggers schema migration."""
from __future__ import annotations

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from rapidcull.schema import CURRENT_SCHEMA_VERSION, get_schema_version


@pytest.fixture()
def fresh_db(tmp_path: Path) -> Path:
    return tmp_path / "rapidcull.db"


def test_startup_creates_schema_on_fresh_db(fresh_db: Path) -> None:
    """TestClient triggers startup; schema should be at CURRENT_SCHEMA_VERSION after."""
    os.environ["RAPIDCULL_DB_PATH"] = str(fresh_db)
    try:
        # Import create_app after env is set so module-level _make_app isn't stale.
        from rapidcull.api import create_app

        app = create_app(db_path=fresh_db)
        with TestClient(app) as client:
            # Trigger at least one request so startup fires.
            client.get("/api/v1/images")  # may 404 — that's fine
        assert get_schema_version(fresh_db) == CURRENT_SCHEMA_VERSION
    finally:
        os.environ.pop("RAPIDCULL_DB_PATH", None)


def test_startup_is_idempotent_on_current_schema(fresh_db: Path) -> None:
    """Running startup twice on same DB must not error."""
    from rapidcull.api import create_app
    from rapidcull.schema import create_or_validate_schema

    # Pre-seed full schema.
    create_or_validate_schema(fresh_db)

    app = create_app(db_path=fresh_db)
    with TestClient(app) as client:
        client.get("/api/v1/images")

    assert get_schema_version(fresh_db) == CURRENT_SCHEMA_VERSION
