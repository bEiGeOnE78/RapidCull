from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from rapidcull.identity import create_image_record, fetch_image_record
from rapidcull.ingest import build_file_fingerprint, discover_supported_media, plan_ingest_actions
from rapidcull.models import FailedIngestItem, IngestRunSummary
from rapidcull.schema import (
    CURRENT_SCHEMA_VERSION,
    SchemaVersionMismatchError,
    create_or_validate_schema,
)
from rapidcull.summaries import build_ingest_run_summary


@pytest.mark.fr
@pytest.mark.integration
def test_fr_001_initializes_schema_on_first_run(tmp_path: Path) -> None:
    db_path = tmp_path / "rapidcull.db"

    create_or_validate_schema(db_path)

    assert db_path.exists()


@pytest.mark.fr
@pytest.mark.integration
def test_fr_001_reports_actionable_error_on_schema_mismatch(tmp_path: Path) -> None:
    db_path = tmp_path / "rapidcull.db"
    create_or_validate_schema(db_path)

    with sqlite3.connect(db_path) as conn:
        conn.execute("UPDATE schema_version SET version = ?", (CURRENT_SCHEMA_VERSION + 1,))
        conn.commit()

    with pytest.raises(SchemaVersionMismatchError) as mismatch_error:
        create_or_validate_schema(db_path)

    assert "migration" in str(mismatch_error.value).lower()


@pytest.mark.fr
@pytest.mark.integration
def test_fr_002_discovers_only_supported_media_files(tmp_path: Path) -> None:
    root = tmp_path / "library"
    root.mkdir()

    supported_files = [
        root / "one.jpg",
        root / "two.jpeg",
        root / "three.png",
        root / "four.heic",
        root / "five.mp4",
    ]
    unsupported_files = [root / "notes.txt", root / "archive.zip"]

    for file_path in supported_files + unsupported_files:
        file_path.write_text("fixture")

    discovered = discover_supported_media([root])

    assert set(discovered) == set(supported_files)


@pytest.mark.fr
@pytest.mark.integration
def test_fr_003_supports_incremental_processing_and_force_mode(tmp_path: Path) -> None:
    root = tmp_path / "library"
    root.mkdir()

    first = root / "first.jpg"
    second = root / "second.jpg"
    first.write_text("a")
    second.write_text("b")

    discovered = discover_supported_media([root])
    first_plan = plan_ingest_actions(discovered, known_fingerprints={}, force_reprocess=False)

    assert set(first_plan.to_process) == {first, second}
    assert first_plan.skipped == []

    known = {path: build_file_fingerprint(path) for path in discovered}
    second_plan = plan_ingest_actions(discovered, known_fingerprints=known, force_reprocess=False)

    assert second_plan.to_process == []
    assert set(second_plan.skipped) == {first, second}

    first.write_text("updated")
    changed_plan = plan_ingest_actions(discovered, known_fingerprints=known, force_reprocess=False)

    assert changed_plan.to_process == [first]
    assert changed_plan.skipped == [second]

    force_plan = plan_ingest_actions(discovered, known_fingerprints=known, force_reprocess=True)

    assert set(force_plan.to_process) == {first, second}
    assert force_plan.skipped == []


@pytest.mark.fr
@pytest.mark.integration
def test_fr_004_image_id_is_stable_across_reprocessing(tmp_path: Path) -> None:
    db_path = tmp_path / "rapidcull.db"
    create_or_validate_schema(db_path)

    media = tmp_path / "asset.jpg"
    media.write_text("content")

    created = create_image_record(db_path, media)
    fetched = fetch_image_record(db_path, media)

    assert fetched is not None
    assert created.image_id == fetched.image_id

    created_again = create_image_record(db_path, media)

    assert created_again.image_id == created.image_id


@pytest.mark.fr
@pytest.mark.integration
def test_fr_005_builds_run_summary_with_failed_items_and_reason() -> None:
    failed_items = [
        FailedIngestItem(path="/library/corrupt.jpg", reason="Unreadable metadata"),
        FailedIngestItem(path="/library/locked.heic", reason="Permission denied"),
    ]

    summary = build_ingest_run_summary(
        processed_count=10,
        skipped_count=3,
        failed_items=failed_items,
    )

    assert summary == IngestRunSummary(
        processed_count=10,
        skipped_count=3,
        failed_count=2,
        failed_items=failed_items,
    )
