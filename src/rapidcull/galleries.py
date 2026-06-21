from __future__ import annotations

import base64
import json
import os
import shutil
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import TypedDict

from rapidcull.models import (
    GalleriesIndexEntry,
    GalleriesIndexFailure,
    GalleriesIndexRebuildResult,
    Gallery,
    GalleryCreationResult,
    GalleryDeleteResult,
    GalleryFailedItem,
    GalleryMetadataRebuildResult,
    GalleryMetadataRebuildSummary,
    GalleryMutationError,
    GalleryRenameResult,
)
from rapidcull.schema import connect


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


# ---------------------------------------------------------------------------
# User gallery DB CRUD (schema v7: galleries + gallery_memberships tables)
# ---------------------------------------------------------------------------


def _encode_source_gallery_id(dir_path: str) -> str:
    """Encode a directory path to a URL-safe base64 gallery_id.

    Mirrors api_galleries._encode_gallery_id so IDs are consistent.
    # TODO(wave2): extract to a shared helper so api_galleries and this module
    # share a single encoding function.
    """
    return base64.urlsafe_b64encode(dir_path.encode()).decode()


def create_user_gallery(
    db_path: Path,
    name: str,
    source: str = "manual",
    image_ids: list[str] | None = None,
) -> Gallery:
    """Create a user gallery row.

    Optionally add initial memberships in a single transaction.
    Returns the new Gallery dataclass.
    """
    gallery_id = uuid.uuid4().hex
    now = datetime.now(UTC).isoformat()

    with connect(db_path) as conn:
        conn.execute(
            "INSERT INTO galleries (gallery_id, name, created_at, source) VALUES (?, ?, ?, ?)",
            (gallery_id, name, now, source),
        )
        if image_ids:
            conn.executemany(
                "INSERT OR IGNORE INTO gallery_memberships (gallery_id, image_id, added_at)"
                " VALUES (?, ?, ?)",
                [(gallery_id, image_id, now) for image_id in image_ids],
            )
        conn.commit()

    count = len(image_ids) if image_ids else 0
    return Gallery(
        gallery_id=gallery_id,
        name=name,
        created_at=now,
        source=source,
        type="user",
        count=count,
    )


def add_to_gallery(db_path: Path, gallery_id: str, image_ids: list[str]) -> int:
    """Insert memberships via INSERT OR IGNORE.

    Returns the number of rows actually added (ignores duplicates).
    """
    if not image_ids:
        return 0

    now = datetime.now(UTC).isoformat()
    with connect(db_path) as conn:
        before: int = conn.execute(
            "SELECT COUNT(*) FROM gallery_memberships WHERE gallery_id = ?", (gallery_id,)
        ).fetchone()[0]
        conn.executemany(
            "INSERT OR IGNORE INTO gallery_memberships (gallery_id, image_id, added_at)"
            " VALUES (?, ?, ?)",
            [(gallery_id, image_id, now) for image_id in image_ids],
        )
        conn.commit()
        after: int = conn.execute(
            "SELECT COUNT(*) FROM gallery_memberships WHERE gallery_id = ?", (gallery_id,)
        ).fetchone()[0]

    return after - before


def remove_from_gallery(db_path: Path, gallery_id: str, image_ids: list[str]) -> int:
    """Delete memberships for the given image_ids from a user gallery.

    Raises ValueError if gallery_id doesn't exist in the `galleries` table
    (source-dir and virtual galleries have synthetic IDs that won't match).
    Returns the number of rows deleted.
    """
    if not image_ids:
        return 0

    with connect(db_path) as conn:
        row = conn.execute(
            "SELECT gallery_id FROM galleries WHERE gallery_id = ?", (gallery_id,)
        ).fetchone()
        if row is None:
            raise ValueError(
                f"gallery_id '{gallery_id}' not found in galleries table. "
                "Remove-from-gallery is only allowed for user galleries."
            )

        placeholders = ",".join("?" for _ in image_ids)
        cursor = conn.execute(
            f"DELETE FROM gallery_memberships WHERE gallery_id = ? AND image_id IN ({placeholders})",
            [gallery_id, *image_ids],
        )
        conn.commit()
        return cursor.rowcount


def delete_user_gallery(db_path: Path, gallery_id: str) -> None:
    """Delete a user gallery row.

    ON DELETE CASCADE (PRAGMA foreign_keys = ON via connect()) clears all
    gallery_memberships rows for this gallery automatically.

    Note: named delete_user_gallery to avoid collision with the existing
    filesystem-based delete_gallery() above. Wave 2: reconcile naming.
    """
    with connect(db_path) as conn:
        conn.execute("DELETE FROM galleries WHERE gallery_id = ?", (gallery_id,))
        conn.commit()


def list_image_galleries(db_path: Path, image_id: str) -> list[Gallery]:
    """Return all galleries the image belongs to.

    Derives the source-dir gallery from images.path, and returns any user
    galleries the image is a member of via gallery_memberships JOIN.
    """
    result: list[Gallery] = []

    with connect(db_path) as conn:
        # Source-dir gallery: derive from images.path dirname
        path_row = conn.execute(
            "SELECT path FROM images WHERE image_id = ?", (image_id,)
        ).fetchone()

        if path_row is not None:
            dir_path = os.path.dirname(path_row[0])
            dir_name = os.path.basename(dir_path) or dir_path
            source_gallery_id = _encode_source_gallery_id(dir_path)
            # Count images in same directory
            count_row = conn.execute(
                "SELECT COUNT(*) FROM images WHERE path LIKE ?", (dir_path + "/%",)
            ).fetchone()
            source_count: int = count_row[0] if count_row else 0
            result.append(
                Gallery(
                    gallery_id=source_gallery_id,
                    name=dir_name,
                    created_at="",  # source-dir galleries have no creation timestamp
                    source="directory",
                    type="source",
                    count=source_count,
                )
            )

        # User galleries via membership JOIN
        user_rows = conn.execute(
            """
            SELECT g.gallery_id, g.name, g.created_at, g.source,
                   COUNT(gm2.image_id) AS member_count
            FROM galleries g
            JOIN gallery_memberships gm ON g.gallery_id = gm.gallery_id
            LEFT JOIN gallery_memberships gm2 ON g.gallery_id = gm2.gallery_id
            WHERE gm.image_id = ?
            GROUP BY g.gallery_id, g.name, g.created_at, g.source
            ORDER BY g.name
            """,
            (image_id,),
        ).fetchall()

        for row in user_rows:
            result.append(
                Gallery(
                    gallery_id=row[0],
                    name=row[1],
                    created_at=row[2],
                    source=row[3],
                    type="user",
                    count=row[4],
                )
            )

    return result
