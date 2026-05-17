from __future__ import annotations

from pathlib import Path

import pytest

from rapidcull.galleries import create_virtual_gallery_hardlinks
from rapidcull.models import GalleryCreationResult


@pytest.mark.fr
@pytest.mark.integration
def test_fr_012_creates_gallery_hardlinks_without_modifying_masters(tmp_path: Path) -> None:
    masters_dir = tmp_path / "masters"
    masters_dir.mkdir()

    first_master = masters_dir / "first.jpg"
    second_master = masters_dir / "second.jpg"

    first_master.write_text("first-master-content")
    second_master.write_text("second-master-content")

    first_before_stat = first_master.stat()
    second_before_stat = second_master.stat()
    first_before_content = first_master.read_text()
    second_before_content = second_master.read_text()

    gallery_dir = tmp_path / "galleries" / "review-set"

    result = create_virtual_gallery_hardlinks(
        gallery_dir=gallery_dir,
        source_paths=[first_master, second_master],
    )

    first_link = gallery_dir / first_master.name
    second_link = gallery_dir / second_master.name

    assert result == GalleryCreationResult(
        gallery_path=str(gallery_dir.resolve()),
        created_paths=[str(first_link.resolve()), str(second_link.resolve())],
        skipped_paths=[],
        failed_items=[],
    )

    assert first_link.exists()
    assert second_link.exists()

    assert first_link.stat().st_ino == first_master.stat().st_ino
    assert first_link.stat().st_dev == first_master.stat().st_dev
    assert second_link.stat().st_ino == second_master.stat().st_ino
    assert second_link.stat().st_dev == second_master.stat().st_dev

    assert first_master.read_text() == first_before_content
    assert second_master.read_text() == second_before_content
    assert first_master.stat().st_mtime_ns == first_before_stat.st_mtime_ns
    assert second_master.stat().st_mtime_ns == second_before_stat.st_mtime_ns
