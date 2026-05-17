from __future__ import annotations

from pathlib import Path

import pytest

from rapidcull.galleries import delete_gallery, rename_gallery
from rapidcull.models import GalleryDeleteResult, GalleryMutationError, GalleryRenameResult


@pytest.mark.fr
@pytest.mark.integration
@pytest.mark.security
def test_fr_016_rename_gallery_allows_in_scope_paths(tmp_path: Path) -> None:
    galleries_root = tmp_path / "galleries"
    source_gallery = galleries_root / "review"
    source_gallery.mkdir(parents=True)
    (source_gallery / "image.jpg").write_text("asset")

    result = rename_gallery(
        gallery_dir=source_gallery,
        new_name="review-renamed",
        allowlist_roots=[galleries_root],
    )

    destination_gallery = galleries_root / "review-renamed"
    assert result == GalleryRenameResult(
        ok=True,
        old_gallery_path=str(source_gallery.resolve()),
        new_gallery_path=str(destination_gallery.resolve()),
        error=None,
    )
    assert not source_gallery.exists()
    assert destination_gallery.exists()
    assert (destination_gallery / "image.jpg").exists()


@pytest.mark.fr
@pytest.mark.integration
@pytest.mark.security
def test_fr_016_rename_gallery_rejects_traversal_name(tmp_path: Path) -> None:
    galleries_root = tmp_path / "galleries"
    source_gallery = galleries_root / "review"
    source_gallery.mkdir(parents=True)

    result = rename_gallery(
        gallery_dir=source_gallery,
        new_name="../escape",
        allowlist_roots=[galleries_root],
    )

    assert result == GalleryRenameResult(
        ok=False,
        old_gallery_path=str(source_gallery.resolve()),
        new_gallery_path=None,
        error=GalleryMutationError(
            code="invalid_name",
            message="Invalid gallery name",
            path=str(source_gallery.resolve()),
        ),
    )


@pytest.mark.fr
@pytest.mark.integration
@pytest.mark.security
def test_fr_016_delete_gallery_allows_in_scope_paths(tmp_path: Path) -> None:
    galleries_root = tmp_path / "galleries"
    target_gallery = galleries_root / "review"
    target_gallery.mkdir(parents=True)
    (target_gallery / "image.jpg").write_text("asset")

    result = delete_gallery(
        gallery_dir=target_gallery,
        allowlist_roots=[galleries_root],
    )

    assert result == GalleryDeleteResult(
        ok=True,
        gallery_path=str(target_gallery.resolve()),
        error=None,
    )
    assert not target_gallery.exists()


@pytest.mark.fr
@pytest.mark.integration
@pytest.mark.security
def test_fr_016_delete_gallery_rejects_out_of_scope_path(tmp_path: Path) -> None:
    galleries_root = tmp_path / "galleries"
    galleries_root.mkdir(parents=True)

    outside_gallery = tmp_path / "outside" / "rogue"
    outside_gallery.mkdir(parents=True)

    result = delete_gallery(
        gallery_dir=outside_gallery,
        allowlist_roots=[galleries_root],
    )

    assert result == GalleryDeleteResult(
        ok=False,
        gallery_path=str(outside_gallery.resolve()),
        error=GalleryMutationError(
            code="outside_allowlist",
            message="Gallery path is outside allowlist",
            path=str(outside_gallery.resolve()),
        ),
    )


@pytest.mark.fr
@pytest.mark.integration
@pytest.mark.security
def test_fr_016_rename_gallery_rejects_empty_name(tmp_path: Path) -> None:
    galleries_root = tmp_path / "galleries"
    source_gallery = galleries_root / "review"
    source_gallery.mkdir(parents=True)

    result = rename_gallery(
        gallery_dir=source_gallery,
        new_name="   ",
        allowlist_roots=[galleries_root],
    )

    assert result == GalleryRenameResult(
        ok=False,
        old_gallery_path=str(source_gallery.resolve()),
        new_gallery_path=None,
        error=GalleryMutationError(
            code="invalid_name",
            message="Invalid gallery name",
            path=str(source_gallery.resolve()),
        ),
    )


@pytest.mark.fr
@pytest.mark.integration
@pytest.mark.security
def test_fr_016_rename_gallery_rejects_destination_conflict(tmp_path: Path) -> None:
    galleries_root = tmp_path / "galleries"
    source_gallery = galleries_root / "review"
    destination_gallery = galleries_root / "review-renamed"
    source_gallery.mkdir(parents=True)
    destination_gallery.mkdir(parents=True)

    result = rename_gallery(
        gallery_dir=source_gallery,
        new_name="review-renamed",
        allowlist_roots=[galleries_root],
    )

    assert result == GalleryRenameResult(
        ok=False,
        old_gallery_path=str(source_gallery.resolve()),
        new_gallery_path=str(destination_gallery.resolve()),
        error=GalleryMutationError(
            code="conflict",
            message="Destination gallery already exists",
            path=str(destination_gallery.resolve()),
        ),
    )


@pytest.mark.fr
@pytest.mark.integration
@pytest.mark.security
def test_fr_016_delete_gallery_rejects_missing_path(tmp_path: Path) -> None:
    galleries_root = tmp_path / "galleries"
    galleries_root.mkdir(parents=True)

    missing_gallery = galleries_root / "missing"

    result = delete_gallery(
        gallery_dir=missing_gallery,
        allowlist_roots=[galleries_root],
    )

    assert result == GalleryDeleteResult(
        ok=False,
        gallery_path=str(missing_gallery.resolve()),
        error=GalleryMutationError(
            code="not_found",
            message="Gallery path does not exist",
            path=str(missing_gallery.resolve()),
        ),
    )
