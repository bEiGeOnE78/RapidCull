from __future__ import annotations

from pathlib import Path

import pytest

from rapidcull.galleries import create_gallery_from_mode
from rapidcull.models import GalleryCreationResult


@pytest.mark.fr
@pytest.mark.integration
def test_fr_013_creates_gallery_from_query_picks_and_face_sample_modes(tmp_path: Path) -> None:
    masters_dir = tmp_path / "masters"
    masters_dir.mkdir()

    first = masters_dir / "first.jpg"
    second = masters_dir / "second.jpg"
    third = masters_dir / "third.jpg"

    for asset in [first, second, third]:
        asset.write_text(f"content-{asset.name}")

    available_assets_by_mode = {
        "query": [first, second],
        "picks": [second],
        "face_samples": [third],
    }

    query_gallery = tmp_path / "galleries" / "query"
    picks_gallery = tmp_path / "galleries" / "picks"
    face_gallery = tmp_path / "galleries" / "face-samples"

    query_result = create_gallery_from_mode(
        gallery_dir=query_gallery,
        mode="query",
        available_assets_by_mode=available_assets_by_mode,
    )
    picks_result = create_gallery_from_mode(
        gallery_dir=picks_gallery,
        mode="picks",
        available_assets_by_mode=available_assets_by_mode,
    )
    face_result = create_gallery_from_mode(
        gallery_dir=face_gallery,
        mode="face_samples",
        available_assets_by_mode=available_assets_by_mode,
    )

    assert query_result == GalleryCreationResult(
        gallery_path=str(query_gallery.resolve()),
        created_paths=[
            str((query_gallery / first.name).resolve()),
            str((query_gallery / second.name).resolve()),
        ],
        skipped_paths=[],
        failed_items=[],
    )
    assert picks_result == GalleryCreationResult(
        gallery_path=str(picks_gallery.resolve()),
        created_paths=[str((picks_gallery / second.name).resolve())],
        skipped_paths=[],
        failed_items=[],
    )
    assert face_result == GalleryCreationResult(
        gallery_path=str(face_gallery.resolve()),
        created_paths=[str((face_gallery / third.name).resolve())],
        skipped_paths=[],
        failed_items=[],
    )


@pytest.mark.fr
@pytest.mark.integration
def test_fr_013_returns_valid_empty_gallery_with_message_when_mode_matches_no_assets(
    tmp_path: Path,
) -> None:
    gallery_dir = tmp_path / "galleries" / "empty-query"

    result = create_gallery_from_mode(
        gallery_dir=gallery_dir,
        mode="query",
        available_assets_by_mode={"query": []},
    )

    assert result == GalleryCreationResult(
        gallery_path=str(gallery_dir.resolve()),
        created_paths=[],
        skipped_paths=[],
        failed_items=[],
    )
    assert gallery_dir.exists()
    assert list(gallery_dir.iterdir()) == []
