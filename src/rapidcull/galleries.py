from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import TypedDict

from rapidcull.models import (
    GalleriesIndexEntry,
    GalleriesIndexFailure,
    GalleriesIndexRebuildResult,
    GalleryCreationResult,
    GalleryDeleteResult,
    GalleryFailedItem,
    GalleryMetadataRebuildResult,
    GalleryMetadataRebuildSummary,
    GalleryMutationError,
    GalleryRenameResult,
)


class GalleryMetadataPayload(TypedDict):
    gallery_path: str
    asset_count: int
    assets: list[str]


class GalleriesIndexPayload(TypedDict):
    gallery_count: int
    galleries: list[GalleryMetadataPayload]


def _is_in_allowlist(path: Path, allowlist_roots: list[Path]) -> bool:
    resolved_path = path.resolve()
    for allowlist_root in allowlist_roots:
        resolved_root = allowlist_root.resolve()
        if resolved_path == resolved_root or resolved_root in resolved_path.parents:
            return True
    return False


def _resolve_rename_destination(gallery_dir: Path, new_name: str) -> Path | None:
    stripped_name = new_name.strip()
    if not stripped_name:
        return None
    if any(separator in stripped_name for separator in ["/", "\\"]):
        return None

    destination = gallery_dir.parent / stripped_name
    if destination != destination.resolve().parent / destination.name:
        return None
    return destination


def rename_gallery(
    gallery_dir: Path,
    new_name: str,
    allowlist_roots: list[Path],
) -> GalleryRenameResult:
    source = gallery_dir.resolve()
    destination = _resolve_rename_destination(gallery_dir=gallery_dir, new_name=new_name)

    if destination is None:
        return GalleryRenameResult(
            ok=False,
            old_gallery_path=str(source),
            new_gallery_path=None,
            error=GalleryMutationError(
                code="invalid_name",
                message="Invalid gallery name",
                path=str(source),
            ),
        )

    if not _is_in_allowlist(path=source, allowlist_roots=allowlist_roots):
        return GalleryRenameResult(
            ok=False,
            old_gallery_path=str(source),
            new_gallery_path=str(destination.resolve()),
            error=GalleryMutationError(
                code="outside_allowlist",
                message="Gallery path is outside allowlist",
                path=str(source),
            ),
        )
    if not _is_in_allowlist(path=destination, allowlist_roots=allowlist_roots):
        return GalleryRenameResult(
            ok=False,
            old_gallery_path=str(source),
            new_gallery_path=str(destination.resolve()),
            error=GalleryMutationError(
                code="outside_allowlist",
                message="Gallery path is outside allowlist",
                path=str(destination.resolve()),
            ),
        )

    if destination.exists():
        return GalleryRenameResult(
            ok=False,
            old_gallery_path=str(source),
            new_gallery_path=str(destination.resolve()),
            error=GalleryMutationError(
                code="conflict",
                message="Destination gallery already exists",
                path=str(destination.resolve()),
            ),
        )

    if not gallery_dir.exists():
        return GalleryRenameResult(
            ok=False,
            old_gallery_path=str(source),
            new_gallery_path=str(destination.resolve()),
            error=GalleryMutationError(
                code="not_found",
                message="Gallery path does not exist",
                path=str(source),
            ),
        )

    try:
        gallery_dir.rename(destination)
    except OSError:
        return GalleryRenameResult(
            ok=False,
            old_gallery_path=str(source),
            new_gallery_path=str(destination.resolve()),
            error=GalleryMutationError(
                code="operation_failed",
                message="Failed to rename gallery",
                path=str(source),
            ),
        )

    return GalleryRenameResult(
        ok=True,
        old_gallery_path=str(source),
        new_gallery_path=str(destination.resolve()),
        error=None,
    )


def delete_gallery(
    gallery_dir: Path,
    allowlist_roots: list[Path],
) -> GalleryDeleteResult:
    resolved_gallery = gallery_dir.resolve()

    if not _is_in_allowlist(path=resolved_gallery, allowlist_roots=allowlist_roots):
        return GalleryDeleteResult(
            ok=False,
            gallery_path=str(resolved_gallery),
            error=GalleryMutationError(
                code="outside_allowlist",
                message="Gallery path is outside allowlist",
                path=str(resolved_gallery),
            ),
        )

    if not gallery_dir.exists():
        return GalleryDeleteResult(
            ok=False,
            gallery_path=str(resolved_gallery),
            error=GalleryMutationError(
                code="not_found",
                message="Gallery path does not exist",
                path=str(resolved_gallery),
            ),
        )

    try:
        shutil.rmtree(gallery_dir)
    except OSError:
        return GalleryDeleteResult(
            ok=False,
            gallery_path=str(resolved_gallery),
            error=GalleryMutationError(
                code="operation_failed",
                message="Failed to delete gallery",
                path=str(resolved_gallery),
            ),
        )

    return GalleryDeleteResult(
        ok=True,
        gallery_path=str(resolved_gallery),
        error=None,
    )


def create_virtual_gallery_hardlinks(
    gallery_dir: Path,
    source_paths: list[Path],
) -> GalleryCreationResult:
    gallery_dir.mkdir(parents=True, exist_ok=True)

    created_paths: list[str] = []
    skipped_paths: list[str] = []
    failed_items: list[GalleryFailedItem] = []

    for source_path in source_paths:
        link_path = gallery_dir / source_path.name

        if link_path.exists():
            skipped_paths.append(str(link_path.resolve()))
            continue

        try:
            link_path.hardlink_to(source_path)
            created_paths.append(str(link_path.resolve()))
        except OSError as error:
            failed_items.append(
                GalleryFailedItem(path=str(source_path.resolve()), reason=str(error))
            )

    return GalleryCreationResult(
        gallery_path=str(gallery_dir.resolve()),
        created_paths=created_paths,
        skipped_paths=skipped_paths,
        failed_items=failed_items,
    )


def create_gallery_from_mode(
    gallery_dir: Path,
    mode: str,
    available_assets_by_mode: dict[str, list[Path]],
) -> GalleryCreationResult:
    selected_assets = available_assets_by_mode.get(mode, [])

    if not selected_assets:
        gallery_dir.mkdir(parents=True, exist_ok=True)
        return GalleryCreationResult(
            gallery_path=str(gallery_dir.resolve()),
            created_paths=[],
            skipped_paths=[],
            failed_items=[],
        )

    return create_virtual_gallery_hardlinks(
        gallery_dir=gallery_dir,
        source_paths=selected_assets,
    )


def rebuild_gallery_metadata(gallery_dir: Path) -> GalleryMetadataRebuildResult:
    if not gallery_dir.exists():
        raise FileNotFoundError(f"Gallery path does not exist: {gallery_dir}")

    metadata_path = gallery_dir / "gallery.json"
    asset_paths = sorted(
        [
            asset_path.resolve()
            for asset_path in gallery_dir.iterdir()
            if asset_path.is_file() and asset_path.name != metadata_path.name
        ]
    )

    payload: GalleryMetadataPayload = {
        "gallery_path": str(gallery_dir.resolve()),
        "asset_count": len(asset_paths),
        "assets": [str(asset_path) for asset_path in asset_paths],
    }
    metadata_path.write_text(json.dumps(payload, indent=2))

    return GalleryMetadataRebuildResult(
        gallery_path=str(gallery_dir.resolve()),
        metadata_path=str(metadata_path.resolve()),
        asset_count=len(asset_paths),
    )


def rebuild_all_galleries_metadata(galleries_root: Path) -> GalleryMetadataRebuildSummary:
    rebuilt_results = [
        rebuild_gallery_metadata(gallery_dir=gallery_dir)
        for gallery_dir in sorted(path for path in galleries_root.iterdir() if path.is_dir())
    ]

    return GalleryMetadataRebuildSummary(rebuilt=rebuilt_results)


def rebuild_galleries_index(galleries_root: Path) -> GalleriesIndexRebuildResult:
    metadata_entries: list[GalleriesIndexEntry] = []
    failures: list[GalleriesIndexFailure] = []
    skipped_count = 0
    processed_count = 0

    gallery_dirs = sorted(p for p in galleries_root.iterdir() if p.is_dir())
    for gallery_dir in gallery_dirs:
        processed_count += 1
        metadata_path = gallery_dir / "gallery.json"
        if not metadata_path.exists():
            skipped_count += 1
            continue

        try:
            payload = json.loads(metadata_path.read_text())
        except json.JSONDecodeError:
            failures.append(
                GalleriesIndexFailure(
                    gallery_path=str(gallery_dir.resolve()),
                    reason="invalid_metadata_json",
                )
            )
            continue

        metadata_entries.append(
            GalleriesIndexEntry(
                gallery_path=str(payload["gallery_path"]),
                asset_count=int(payload["asset_count"]),
                assets=[str(asset_path) for asset_path in payload["assets"]],
            )
        )

    sorted_entries = sorted(metadata_entries, key=lambda entry: entry.gallery_path)
    index_path = galleries_root / "galleries_index.json"
    index_payload: GalleriesIndexPayload = {
        "gallery_count": len(sorted_entries),
        "galleries": [
            {
                "gallery_path": entry.gallery_path,
                "asset_count": entry.asset_count,
                "assets": entry.assets,
            }
            for entry in sorted_entries
        ],
    }
    index_path.write_text(json.dumps(index_payload, indent=2))

    return GalleriesIndexRebuildResult(
        index_path=str(index_path.resolve()),
        gallery_count=len(sorted_entries),
        processed_count=processed_count,
        skipped_count=skipped_count,
        failed_count=len(failures),
        failures=failures,
    )
