from __future__ import annotations

import json
from pathlib import Path

import pytest

from rapidcull.galleries import rebuild_all_galleries_metadata, rebuild_gallery_metadata
from rapidcull.models import GalleryMetadataRebuildResult, GalleryMetadataRebuildSummary


@pytest.mark.fr
@pytest.mark.integration
def test_fr_014_rebuilds_single_gallery_metadata_json(tmp_path: Path) -> None:
    gallery_dir = tmp_path / "galleries" / "review"
    gallery_dir.mkdir(parents=True)

    first = gallery_dir / "first.jpg"
    second = gallery_dir / "second.jpg"
    first.write_text("asset-1")
    second.write_text("asset-2")

    metadata_path = gallery_dir / "gallery.json"
    metadata_path.write_text('{"stale": true}')

    result = rebuild_gallery_metadata(gallery_dir=gallery_dir)

    assert result == GalleryMetadataRebuildResult(
        gallery_path=str(gallery_dir.resolve()),
        metadata_path=str(metadata_path.resolve()),
        asset_count=2,
    )

    rebuilt_payload = json.loads(metadata_path.read_text())
    assert rebuilt_payload == {
        "gallery_path": str(gallery_dir.resolve()),
        "asset_count": 2,
        "assets": [
            str(first.resolve()),
            str(second.resolve()),
        ],
    }


@pytest.mark.fr
@pytest.mark.integration
def test_fr_014_returns_explicit_error_for_missing_gallery_path(tmp_path: Path) -> None:
    missing_gallery = tmp_path / "galleries" / "missing"

    with pytest.raises(FileNotFoundError, match="Gallery path does not exist"):
        rebuild_gallery_metadata(gallery_dir=missing_gallery)


@pytest.mark.fr
@pytest.mark.integration
def test_fr_014_rebuilds_metadata_for_all_galleries(tmp_path: Path) -> None:
    galleries_root = tmp_path / "galleries"
    review_gallery = galleries_root / "review"
    picks_gallery = galleries_root / "picks"
    review_gallery.mkdir(parents=True)
    picks_gallery.mkdir(parents=True)

    (review_gallery / "first.jpg").write_text("review-1")
    (review_gallery / "second.jpg").write_text("review-2")
    (picks_gallery / "third.jpg").write_text("picks-1")

    (review_gallery / "gallery.json").write_text('{"stale": true}')
    (picks_gallery / "gallery.json").write_text('{"stale": true}')

    summary = rebuild_all_galleries_metadata(galleries_root=galleries_root)

    assert summary == GalleryMetadataRebuildSummary(
        rebuilt=[
            GalleryMetadataRebuildResult(
                gallery_path=str(picks_gallery.resolve()),
                metadata_path=str((picks_gallery / "gallery.json").resolve()),
                asset_count=1,
            ),
            GalleryMetadataRebuildResult(
                gallery_path=str(review_gallery.resolve()),
                metadata_path=str((review_gallery / "gallery.json").resolve()),
                asset_count=2,
            ),
        ]
    )

    picks_payload = json.loads((picks_gallery / "gallery.json").read_text())
    review_payload = json.loads((review_gallery / "gallery.json").read_text())

    assert picks_payload == {
        "gallery_path": str(picks_gallery.resolve()),
        "asset_count": 1,
        "assets": [str((picks_gallery / "third.jpg").resolve())],
    }
    assert review_payload == {
        "gallery_path": str(review_gallery.resolve()),
        "asset_count": 2,
        "assets": [
            str((review_gallery / "first.jpg").resolve()),
            str((review_gallery / "second.jpg").resolve()),
        ],
    }
