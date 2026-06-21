"""FastAPI router for gallery list and gallery-image endpoints.

A "gallery" is one of:
  - source-dir: unique directory path grouping ingested images (derived, read-only)
  - user: user-defined named collection stored in the `galleries` table
  - virtual: always-present filter views (picks, rejects, trash)

Gallery IDs:
  - source-dir: URL-safe base64 of the directory path
  - user: UUID hex stored in `galleries.gallery_id`
  - virtual: literal strings 'virtual:picks', 'virtual:rejects', 'virtual:trash'

All responses use the standard {ok, data|error} envelope from api_envelope.py.
"""

from __future__ import annotations

import base64
import os
from pathlib import Path
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from rapidcull.api_envelope import ApiError, ok
from rapidcull.galleries import (
    add_to_gallery,
    create_user_gallery,
    delete_user_gallery,
    remove_from_gallery,
)
from rapidcull.schema import connect

router = APIRouter()

_db_path: Path | None = None

VIRTUAL_PICKS = "virtual:picks"
VIRTUAL_REJECTS = "virtual:rejects"
VIRTUAL_TRASH = "virtual:trash"
VIRTUAL_IDS = {VIRTUAL_PICKS, VIRTUAL_REJECTS, VIRTUAL_TRASH}


def configure_router(db_path: Path) -> None:
    """Set the DB path used by all gallery endpoints."""
    global _db_path
    _db_path = db_path


def _get_db_path() -> Path:
    if _db_path is None:
        raise RuntimeError("api_galleries router not configured with a db_path")
    return _db_path


def _encode_gallery_id(dir_path: str) -> str:
    """Encode a directory path to a URL-safe base64 gallery_id."""
    return base64.urlsafe_b64encode(dir_path.encode()).decode()


def _decode_gallery_id(gallery_id: str) -> str:
    """Decode a URL-safe base64 gallery_id back to a directory path."""
    try:
        return base64.urlsafe_b64decode(gallery_id.encode()).decode()
    except Exception as exc:
        raise ApiError(
            code="GALLERY_NOT_FOUND",
            message=f"Gallery '{gallery_id}' not found.",
            http_status=404,
        ) from exc


def _thumbnail_url(thumbnail_path: str | None, db_path: Path) -> str | None:
    """Convert absolute thumbnail path to /proxies/ URL, or None if unavailable."""
    if not thumbnail_path:
        return None
    proxy_root = db_path.parent / "proxies"
    try:
        rel = Path(thumbnail_path).relative_to(proxy_root)
        return "/proxies/" + str(rel)
    except ValueError:
        return None


def _is_user_gallery(db_path: Path, gallery_id: str) -> bool:
    """Return True if gallery_id exists in the galleries table."""
    with connect(db_path) as conn:
        row = conn.execute(
            "SELECT gallery_id FROM galleries WHERE gallery_id = ?", (gallery_id,)
        ).fetchone()
    return row is not None


# ---------------------------------------------------------------------------
# POST /api/v1/galleries — create a user gallery
# ---------------------------------------------------------------------------


class CreateGalleryRequest(BaseModel):
    name: str


@router.post("/api/v1/galleries", status_code=201)
def create_gallery(request: CreateGalleryRequest) -> dict[str, Any]:
    """Create a named user gallery (manual, empty). Returns the new Gallery."""
    db_path = _get_db_path()
    gallery = create_user_gallery(db_path, name=request.name, source="manual", image_ids=[])
    return ok(
        {
            "gallery_id": gallery.gallery_id,
            "name": gallery.name,
            "created_at": gallery.created_at,
            "source": gallery.source,
            "type": gallery.type,
            "count": gallery.count,
        }
    )


# ---------------------------------------------------------------------------
# GET /api/v1/galleries — union of source + user + virtual
# ---------------------------------------------------------------------------


@router.get("/api/v1/galleries")
def list_galleries() -> dict[str, Any]:
    """List all galleries (source-dir, user, virtual) with counts and types."""
    db_path = _get_db_path()
    galleries: list[dict[str, Any]] = []

    with connect(db_path) as conn:
        # --- Source-dir galleries ---
        rows = conn.execute("SELECT path FROM images ORDER BY path").fetchall()
        counts: dict[str, int] = {}
        for (path,) in rows:
            dir_path = os.path.dirname(path)
            counts[dir_path] = counts.get(dir_path, 0) + 1

        for dir_path, count in sorted(counts.items()):
            galleries.append(
                {
                    "gallery_id": _encode_gallery_id(dir_path),
                    "name": os.path.basename(dir_path) or dir_path,
                    "type": "source",
                    "count": count,
                }
            )

        # --- User galleries ---
        user_rows = conn.execute("""
            SELECT g.gallery_id, g.name, g.created_at, g.source,
                   COUNT(gm.image_id) AS member_count
            FROM galleries g
            LEFT JOIN gallery_memberships gm ON g.gallery_id = gm.gallery_id
            GROUP BY g.gallery_id, g.name, g.created_at, g.source
            ORDER BY g.name
            """).fetchall()

        for row in user_rows:
            galleries.append(
                {
                    "gallery_id": row[0],
                    "name": row[1],
                    "type": "user",
                    "count": row[4],
                }
            )

        # --- Virtual galleries (always present) ---
        # JOIN with images to exclude orphan cull_decisions rows (images deleted via trash).
        picks_count: int = conn.execute(
            "SELECT COUNT(*) FROM cull_decisions c"
            " INNER JOIN images i ON c.image_id = i.image_id"
            " WHERE c.decision = 'pick'"
        ).fetchone()[0]
        rejects_count: int = conn.execute(
            "SELECT COUNT(*) FROM cull_decisions c"
            " INNER JOIN images i ON c.image_id = i.image_id"
            " WHERE c.decision = 'reject'"
        ).fetchone()[0]
        trash_count: int = conn.execute("SELECT COUNT(*) FROM trash").fetchone()[0]

    galleries.append(
        {"gallery_id": VIRTUAL_PICKS, "name": "Picks", "type": "virtual", "count": picks_count}
    )
    galleries.append(
        {
            "gallery_id": VIRTUAL_REJECTS,
            "name": "Rejects",
            "type": "virtual",
            "count": rejects_count,
        }
    )
    galleries.append(
        {"gallery_id": VIRTUAL_TRASH, "name": "Trash", "type": "virtual", "count": trash_count}
    )

    return ok({"galleries": galleries})


# ---------------------------------------------------------------------------
# GET /api/v1/galleries/{gallery_id}/images — branched by type
# ---------------------------------------------------------------------------


@router.get("/api/v1/galleries/{gallery_id}/images")
def get_gallery_images(
    gallery_id: str,
    page: int = 1,
    page_size: int = 50,
) -> dict[str, Any]:
    """List images in a gallery, paginated. Branches by gallery type."""
    db_path = _get_db_path()

    # --- Virtual galleries ---
    if gallery_id in VIRTUAL_IDS:
        return _get_virtual_gallery_images(db_path, gallery_id, page, page_size)

    # --- User gallery ---
    if _is_user_gallery(db_path, gallery_id):
        return _get_user_gallery_images(db_path, gallery_id, page, page_size)

    # --- Source-dir gallery (base64-encoded path) ---
    return _get_source_gallery_images(db_path, gallery_id, page, page_size)


def _build_image_row(row: tuple[Any, ...], db_path: Path) -> dict[str, Any]:
    return {
        "image_id": row[0],
        "path": row[1],
        "thumbnail_path": _thumbnail_url(row[2], db_path),
        "display_path": _thumbnail_url(row[3], db_path),
        "full_path": _thumbnail_url(row[4], db_path),
        "decision": row[5] if len(row) > 5 else None,
    }


def _get_virtual_gallery_images(
    db_path: Path, gallery_id: str, page: int, page_size: int
) -> dict[str, Any]:
    offset = (page - 1) * page_size

    if gallery_id == VIRTUAL_TRASH:
        # Trash: rows come from the trash table (images rows are deleted)
        with connect(db_path) as conn:
            total: int = conn.execute("SELECT COUNT(*) FROM trash").fetchone()[0]
            rows = conn.execute(
                "SELECT image_id, original_path, trashed_at FROM trash"
                " ORDER BY trashed_at LIMIT ? OFFSET ?",
                (page_size, offset),
            ).fetchall()
        images = [
            {
                "image_id": row[0],
                "path": row[1],
                "thumbnail_path": None,
                "display_path": None,
                "full_path": None,
                "decision": None,
                "trashed_at": row[2],
            }
            for row in rows
        ]
        return ok({"images": images, "total": total, "page": page, "page_size": page_size})

    # Picks or Rejects: filter cull_decisions JOIN images (excludes orphan decision rows)
    decision_value = "pick" if gallery_id == VIRTUAL_PICKS else "reject"
    with connect(db_path) as conn:
        total = conn.execute(
            "SELECT COUNT(*) FROM cull_decisions c"
            " INNER JOIN images i ON c.image_id = i.image_id"
            " WHERE c.decision = ?",
            (decision_value,),
        ).fetchone()[0]
        rows = conn.execute(
            """
            SELECT i.image_id, i.path, i.thumbnail_path, i.display_path, i.full_path, cd.decision
            FROM cull_decisions cd
            JOIN images i ON i.image_id = cd.image_id
            WHERE cd.decision = ?
            ORDER BY i.path
            LIMIT ? OFFSET ?
            """,
            (decision_value, page_size, offset),
        ).fetchall()

    images = [_build_image_row(row, db_path) for row in rows]
    return ok({"images": images, "total": total, "page": page, "page_size": page_size})


def _get_user_gallery_images(
    db_path: Path, gallery_id: str, page: int, page_size: int
) -> dict[str, Any]:
    offset = (page - 1) * page_size
    with connect(db_path) as conn:
        total: int = conn.execute(
            "SELECT COUNT(*) FROM gallery_memberships WHERE gallery_id = ?", (gallery_id,)
        ).fetchone()[0]
        rows = conn.execute(
            """
            SELECT i.image_id, i.path, i.thumbnail_path, i.display_path, i.full_path, cd.decision
            FROM gallery_memberships gm
            JOIN images i ON i.image_id = gm.image_id
            LEFT JOIN cull_decisions cd ON i.image_id = cd.image_id
            WHERE gm.gallery_id = ?
            ORDER BY i.path
            LIMIT ? OFFSET ?
            """,
            (gallery_id, page_size, offset),
        ).fetchall()

    images = [_build_image_row(row, db_path) for row in rows]
    return ok({"images": images, "total": total, "page": page, "page_size": page_size})


def _get_source_gallery_images(
    db_path: Path, gallery_id: str, page: int, page_size: int
) -> dict[str, Any]:
    dir_path = _decode_gallery_id(gallery_id)

    with connect(db_path) as conn:
        all_paths = conn.execute("SELECT path FROM images ORDER BY path").fetchall()

    matching = [p for (p,) in all_paths if os.path.dirname(p) == dir_path]
    total = len(matching)

    if total == 0:
        raise ApiError(
            code="GALLERY_NOT_FOUND",
            message=f"Gallery '{gallery_id}' not found.",
            http_status=404,
        )

    offset = (page - 1) * page_size
    page_paths = matching[offset : offset + page_size]

    if not page_paths:
        return ok({"images": [], "total": total, "page": page, "page_size": page_size})

    placeholders = ",".join("?" for _ in page_paths)
    with connect(db_path) as conn:
        rows = conn.execute(
            f"""
            SELECT i.image_id, i.path, i.thumbnail_path, i.display_path, i.full_path, cd.decision
            FROM images i
            LEFT JOIN cull_decisions cd ON i.image_id = cd.image_id
            WHERE i.path IN ({placeholders})
            ORDER BY i.path
            """,
            page_paths,
        ).fetchall()

    images = [_build_image_row(row, db_path) for row in rows]
    return ok({"images": images, "total": total, "page": page, "page_size": page_size})


# ---------------------------------------------------------------------------
# DELETE /api/v1/galleries/{gallery_id} — user galleries only
# ---------------------------------------------------------------------------


@router.delete("/api/v1/galleries/{gallery_id}", status_code=200)
def delete_gallery_endpoint(gallery_id: str) -> dict[str, Any]:
    """Delete a user gallery. Rejects source-dir and virtual galleries."""
    db_path = _get_db_path()

    if gallery_id in VIRTUAL_IDS:
        raise ApiError(
            code="GALLERY_NOT_MUTABLE",
            message="Virtual galleries cannot be deleted.",
            http_status=400,
        )

    if not _is_user_gallery(db_path, gallery_id):
        raise ApiError(
            code="GALLERY_NOT_FOUND",
            message=f"Gallery '{gallery_id}' not found or is a source-dir gallery (not deletable).",
            http_status=404,
        )

    delete_user_gallery(db_path, gallery_id)
    return ok({"gallery_id": gallery_id, "deleted": True})


# ---------------------------------------------------------------------------
# POST /api/v1/galleries/{gallery_id}/images — add images to user gallery
# ---------------------------------------------------------------------------


class AddImagesRequest(BaseModel):
    image_ids: list[str]


@router.post("/api/v1/galleries/{gallery_id}/images", status_code=200)
def add_images_to_gallery(gallery_id: str, request: AddImagesRequest) -> dict[str, Any]:
    """Add images to a user gallery. Rejects source-dir and virtual galleries."""
    db_path = _get_db_path()

    if gallery_id in VIRTUAL_IDS:
        raise ApiError(
            code="GALLERY_NOT_MUTABLE",
            message="Cannot add images to virtual galleries.",
            http_status=400,
        )

    if not _is_user_gallery(db_path, gallery_id):
        raise ApiError(
            code="GALLERY_NOT_FOUND",
            message=f"Gallery '{gallery_id}' not found or is a source-dir gallery.",
            http_status=404,
        )

    added = add_to_gallery(db_path, gallery_id, request.image_ids)
    return ok({"gallery_id": gallery_id, "added_count": added})


# ---------------------------------------------------------------------------
# DELETE /api/v1/galleries/{gallery_id}/images/{image_id}
# ---------------------------------------------------------------------------


@router.delete("/api/v1/galleries/{gallery_id}/images/{image_id}", status_code=200)
def remove_image_from_gallery(gallery_id: str, image_id: str) -> dict[str, Any]:
    """Remove an image from a user gallery. Rejects source-dir and virtual."""
    db_path = _get_db_path()

    if gallery_id in VIRTUAL_IDS:
        raise ApiError(
            code="GALLERY_NOT_MUTABLE",
            message="Cannot remove images from virtual galleries.",
            http_status=400,
        )

    if not _is_user_gallery(db_path, gallery_id):
        raise ApiError(
            code="GALLERY_NOT_FOUND",
            message=f"Gallery '{gallery_id}' not found or is a source-dir gallery.",
            http_status=404,
        )

    try:
        removed = remove_from_gallery(db_path, gallery_id, [image_id])
    except ValueError as exc:
        raise ApiError(
            code="GALLERY_NOT_MUTABLE",
            message=str(exc),
            http_status=400,
        ) from exc

    return ok({"gallery_id": gallery_id, "image_id": image_id, "removed_count": removed})
