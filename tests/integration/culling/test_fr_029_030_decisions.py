"""Integration tests: FR-029 pick/reject persistence, FR-030 cross-session restore."""

import sqlite3
from pathlib import Path

import pytest

from rapidcull.culling import get_decision, list_decisions, set_decision, undo_decision
from rapidcull.schema import create_or_validate_schema


def _add_image(db_path: Path, image_id: str, path: str) -> None:
    with sqlite3.connect(db_path) as conn:
        conn.execute("INSERT INTO images VALUES (?, ?)", (image_id, path))


def test_fr_029_set_decision_persists_pick(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    create_or_validate_schema(db_path)
    _add_image(db_path, "img1", "/photos/a.jpg")

    set_decision(db_path, "img1", "pick")
    decision = get_decision(db_path, "img1")

    assert decision is not None
    assert decision.decision == "pick"
    assert decision.image_id == "img1"


def test_fr_030_decision_survives_reconnect(tmp_path: Path) -> None:
    """FR-030: decisions restore across sessions (new DB connection)."""
    db_path = tmp_path / "test.db"
    create_or_validate_schema(db_path)
    _add_image(db_path, "img1", "/photos/a.jpg")

    set_decision(db_path, "img1", "reject")

    decision = get_decision(db_path, "img1")
    assert decision is not None
    assert decision.decision == "reject"


def test_set_decision_upserts_on_conflict(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    create_or_validate_schema(db_path)
    _add_image(db_path, "img1", "/photos/a.jpg")

    set_decision(db_path, "img1", "reject")
    set_decision(db_path, "img1", "pick")

    decision = get_decision(db_path, "img1")
    assert decision is not None
    assert decision.decision == "pick"


def test_list_decisions_filter_pick(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    create_or_validate_schema(db_path)
    _add_image(db_path, "img1", "/photos/a.jpg")
    _add_image(db_path, "img2", "/photos/b.jpg")
    _add_image(db_path, "img3", "/photos/c.jpg")

    set_decision(db_path, "img1", "pick")
    set_decision(db_path, "img2", "reject")
    set_decision(db_path, "img3", "pick")

    picks = list_decisions(db_path, filter="pick")
    assert {d.image_id for d in picks} == {"img1", "img3"}


def test_list_decisions_filter_reject(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    create_or_validate_schema(db_path)
    _add_image(db_path, "img1", "/photos/a.jpg")
    _add_image(db_path, "img2", "/photos/b.jpg")

    set_decision(db_path, "img1", "pick")
    set_decision(db_path, "img2", "reject")

    rejects = list_decisions(db_path, filter="reject")
    assert len(rejects) == 1
    assert rejects[0].image_id == "img2"


def test_undo_decision_removes_row(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    create_or_validate_schema(db_path)
    _add_image(db_path, "img1", "/photos/a.jpg")

    set_decision(db_path, "img1", "pick")
    undo_decision(db_path, "img1")

    assert get_decision(db_path, "img1") is None


def test_set_decision_unknown_image_raises(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    create_or_validate_schema(db_path)

    with pytest.raises(ValueError, match="image_id not found"):
        set_decision(db_path, "no-such-id", "pick")
