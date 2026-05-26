from __future__ import annotations

import json
from pathlib import Path

import pytest

from rapidcull.galleries import rebuild_galleries_index
from rapidcull.models import GalleriesIndexFailure, GalleriesIndexRebuildResult


@pytest.mark.fr
@pytest.mark.integration
def test_fr_015_rebuilds_central_galleries_index_from_current_gallery_metadata(
    tmp_path: Path,
) -> None:
    galleries_root = tmp_path / "galleries"
    review_gallery = galleries_root / "review"
    picks_gallery = galleries_root / "picks"
    review_gallery.mkdir(parents=True)
    picks_gallery.mkdir(parents=True)

    (review_gallery / "gallery.json").write_text(
        json.dumps(
            {
                "gallery_path": str(review_gallery.resolve()),
                "asset_count": 2,
                "assets": [
                    str((review_gallery / "first.jpg").resolve()),
                    str((review_gallery / "second.jpg").resolve()),
                ],
            }
        )
    )
    (picks_gallery / "gallery.json").write_text(
        json.dumps(
            {
                "gallery_path": str(picks_gallery.resolve()),
                "asset_count": 1,
                "assets": [str((picks_gallery / "third.jpg").resolve())],
            }
        )
    )

    result = rebuild_galleries_index(galleries_root=galleries_root)
    index_path = galleries_root / "galleries_index.json"

    assert result == GalleriesIndexRebuildResult(
        index_path=str(index_path.resolve()),
        gallery_count=2,
        processed_count=2,
        skipped_count=0,
        failed_count=0,
        failures=[],
    )

    payload = json.loads(index_path.read_text())
    assert payload == {
        "gallery_count": 2,
        "galleries": [
            {
                "gallery_path": str(picks_gallery.resolve()),
                "asset_count": 1,
                "assets": [str((picks_gallery / "third.jpg").resolve())],
            },
            {
                "gallery_path": str(review_gallery.resolve()),
                "asset_count": 2,
                "assets": [
                    str((review_gallery / "first.jpg").resolve()),
                    str((review_gallery / "second.jpg").resolve()),
                ],
            },
        ],
    }

    # Idempotence: a second rebuild must produce the same index ordering.
    result2 = rebuild_galleries_index(galleries_root=galleries_root)
    payload2 = json.loads(index_path.read_text())
    assert result2 == result
    assert payload2 == payload


@pytest.mark.fr
@pytest.mark.integration
def test_fr_015_continues_index_rebuild_when_one_gallery_metadata_is_invalid(
    tmp_path: Path,
) -> None:
    galleries_root = tmp_path / "galleries"
    valid_gallery = galleries_root / "valid"
    invalid_gallery = galleries_root / "invalid"
    valid_gallery.mkdir(parents=True)
    invalid_gallery.mkdir(parents=True)

    (valid_gallery / "gallery.json").write_text(
        json.dumps(
            {
                "gallery_path": str(valid_gallery.resolve()),
                "asset_count": 1,
                "assets": [str((valid_gallery / "ok.jpg").resolve())],
            }
        )
    )
    (invalid_gallery / "gallery.json").write_text("{ not valid json")

    result = rebuild_galleries_index(galleries_root=galleries_root)
    index_path = galleries_root / "galleries_index.json"

    assert result == GalleriesIndexRebuildResult(
        index_path=str(index_path.resolve()),
        gallery_count=1,
        processed_count=2,
        skipped_count=0,
        failed_count=1,
        failures=[
            GalleriesIndexFailure(
                gallery_path=str(invalid_gallery.resolve()),
                reason="invalid_metadata_json",
            )
        ],
    )

    payload = json.loads(index_path.read_text())
    assert payload == {
        "gallery_count": 1,
        "galleries": [
            {
                "gallery_path": str(valid_gallery.resolve()),
                "asset_count": 1,
                "assets": [str((valid_gallery / "ok.jpg").resolve())],
            }
        ],
    }
