"""FastAPI router for gallery list and gallery-image endpoints.

A "gallery" is a unique directory path grouping ingested images.
Gallery IDs are URL-safe base64 encodings of the directory path.

All responses use the standard {ok, data|error} envelope from api_envelope.py.
"""

from __future__ import annotations

import base64
import os
import sqlite3
from pathlib import Path
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from rapidcull.api_envelope import ApiError, ok
from rapidcull.galleries import create_gallery_from_mode, create_virtual_gallery_hardlinks
from rapidcull.query_grammar import parse_query

router = APIRouter()

_db_path: Path | None = None


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


class CreateGalleryRequest(BaseModel):
    name: str
    mode: str
    query: str | None = None


@router.post("/api/v1/galleries", status_code=201)
def create_gallery(request: CreateGalleryRequest) -> dict[str, Any]:
    """Create a virtual gallery from picks or a query expression."""
    db_path = _get_db_path()
    gallery_dir = db_path.parent / "galleries" / request.name

    if request.mode == "picks":
        with sqlite3.connect(db_path) as conn:
            rows = conn.execute("""
                SELECT i.path FROM images i
                JOIN cull_decisions cd ON i.image_id = cd.image_id
                WHERE cd.decision = 'pick'
                ORDER BY i.path
                """).fetchall()
        pick_paths = [Path(row[0]) for row in rows]
        result = create_gallery_from_mode(
            gallery_dir,
            "picks",
            {"picks": pick_paths},
        )
        return ok(
            {
                "gallery_path": result.gallery_path,
                "created_count": len(result.created_paths),
            }
        )

    elif request.mode == "query":
        if not request.query:
            raise ApiError(
                code="QUERY_REQUIRED",
                message="A query expression is required when mode is 'query'.",
                http_status=422,
            )
        parse_result = parse_query(request.query)
        if not parse_result.ok or parse_result.expression is None:
            error_messages = "; ".join(e.message for e in parse_result.errors)
            raise ApiError(
                code="QUERY_PARSE_ERROR",
                message=error_messages,
                http_status=422,
            )
        with sqlite3.connect(db_path) as conn:
            rows = conn.execute("SELECT image_id, path FROM images ORDER BY path").fetchall()
        matching_paths = [Path(path) for _, path in rows]
        result = create_virtual_gallery_hardlinks(gallery_dir, matching_paths)
        return ok(
            {
                "gallery_path": result.gallery_path,
                "created_count": len(result.created_paths),
            }
        )

    else:
        raise ApiError(
            code="INVALID_MODE",
            message=f"Unknown gallery mode '{request.mode}'. Expected 'picks' or 'query'.",
            http_status=422,
        )


@router.get("/api/v1/galleries")
def list_galleries() -> dict[str, Any]:
    """List all galleries (unique directories) with image counts."""
    db_path = _get_db_path()

    with sqlite3.connect(db_path) as conn:
        rows = conn.execute("SELECT path FROM images ORDER BY path").fetchall()

    # Group by dirname in Python (SQLite has no dirname())
    counts: dict[str, int] = {}
    for (path,) in rows:
        dir_path = os.path.dirname(path)
        counts[dir_path] = counts.get(dir_path, 0) + 1

    galleries = [
        {
            "gallery_id": _encode_gallery_id(dir_path),
            "name": os.path.basename(dir_path) or dir_path,
            "path": dir_path,
            "image_count": count,
        }
        for dir_path, count in sorted(counts.items())
    ]

    return ok({"galleries": galleries})


@router.get("/api/v1/galleries/{gallery_id}/images")
def get_gallery_images(
    gallery_id: str,
    page: int = 1,
    page_size: int = 50,
) -> dict[str, Any]:
    """List images in a gallery, paginated."""
    db_path = _get_db_path()
    dir_path = _decode_gallery_id(gallery_id)

    # Verify the gallery exists (at least one image in that directory)
    with sqlite3.connect(db_path) as conn:
        count_row = conn.execute(
            "SELECT COUNT(*) FROM images WHERE path LIKE ?",
            (dir_path + "/%",),
        ).fetchone()

    total: int = count_row[0] if count_row else 0

    # Also check for images whose dirname matches exactly (handles root "/" edge case)
    with sqlite3.connect(db_path) as conn:
        all_paths = conn.execute("SELECT path FROM images ORDER BY path").fetchall()

    matching = [p for (p,) in all_paths if os.path.dirname(p) == dir_path]
    total = len(matching)

    if total == 0:
        raise ApiError(
            code="GALLERY_NOT_FOUND",
            message=f"Gallery '{gallery_id}' not found.",
            http_status=404,
        )

    # Paginate
    offset = (page - 1) * page_size
    page_paths = matching[offset : offset + page_size]

    if not page_paths:
        return ok({"images": [], "total": total, "page": page, "page_size": page_size})

    # Fetch image_ids and decisions for the page
    placeholders = ",".join("?" for _ in page_paths)
    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            f"""
            SELECT i.image_id, i.path, cd.decision
            FROM images i
            LEFT JOIN cull_decisions cd ON i.image_id = cd.image_id
            WHERE i.path IN ({placeholders})
            ORDER BY i.path
            """,
            page_paths,
        ).fetchall()

    images = [
        {
            "image_id": row[0],
            "path": row[1],
            "thumbnail_path": None,
            "decision": row[2],
        }
        for row in rows
    ]

    return ok({"images": images, "total": total, "page": page, "page_size": page_size})
