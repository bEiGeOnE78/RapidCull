"""FastAPI router for image search via query grammar.

Route: GET /api/v1/images/search?query=<text>&offset=0&limit=200

Parses the query string using parse_query() from query_grammar.py,
loads all images with person names (via faces JOIN persons), extracts
metadata fields from the JSON metadata column, builds a QueryRecord per
image, filters with evaluate_query(), then paginates and returns results
matching the gallery-images per-image payload shape.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Query

from rapidcull.api_envelope import ApiError, ok
from rapidcull.query_evaluator import QueryRecord, evaluate_query
from rapidcull.query_grammar import parse_query
from rapidcull.schema import connect

router = APIRouter()

_db_path: Path | None = None


def configure_router(db_path: Path) -> None:
    """Set the DB path used by the search endpoint."""
    global _db_path
    _db_path = db_path


def _get_db_path() -> Path:
    if _db_path is None:
        raise RuntimeError("api_search router not configured with a db_path")
    return _db_path


def _thumbnail_url(path: str | None, db_path: Path) -> str | None:
    """Convert absolute proxy path to /proxies/ URL, or None."""
    if not path:
        return None
    proxy_root = db_path.parent / "proxies"
    try:
        from pathlib import PurePosixPath  # noqa: PLC0415

        rel = Path(path).relative_to(proxy_root)
        return "/proxies/" + str(rel)
    except ValueError:
        return None


def _build_query_record(
    image_id: str,
    metadata_json: str | None,
    person_names: list[str],
) -> QueryRecord:
    """Build a QueryRecord dict from DB row data."""
    meta: dict[str, Any] = {}
    if metadata_json:
        try:
            meta = json.loads(metadata_json)
        except (json.JSONDecodeError, ValueError):
            meta = {}

    return {
        "person": person_names,
        "date": meta.get("date") or meta.get("DateTimeOriginal") or meta.get("date_original"),
        "camera": meta.get("camera") or meta.get("Make") or meta.get("model"),
        "lens": meta.get("lens") or meta.get("LensModel") or meta.get("lens_model"),
        "iso": meta.get("iso") or meta.get("ISO"),
        "fnumber": meta.get("fnumber") or meta.get("FNumber") or meta.get("f_number"),
        "focal": meta.get("focal")
        or meta.get("FocalLength")
        or meta.get("focal_length"),
        "keyword": meta.get("keyword") or meta.get("keywords") or [],
    }


@router.get("/api/v1/images/search")
def search_images(
    query: str = Query(default=""),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=200, ge=1, le=1000),
) -> dict[str, Any]:
    """Search images using the RapidCull query grammar.

    Empty query returns all images (paginated).
    Invalid query syntax returns 400 with structured error detail.
    """
    db_path = _get_db_path()

    # --- Parse query ---
    # Empty string: return all images (no filter)
    expression = None
    if query.strip():
        parse_result = parse_query(query)
        if not parse_result.ok or parse_result.expression is None:
            first_error = parse_result.errors[0] if parse_result.errors else None
            raise ApiError(
                code="QUERY_PARSE_ERROR",
                message=first_error.message if first_error else "Query parse failed.",
                details={
                    "code": first_error.code if first_error else "PARSE_ERROR",
                    "message": first_error.message if first_error else "Query parse failed.",
                    "suggestions": first_error.suggestions if first_error else [],
                    "token": first_error.token if first_error else "",
                },
                http_status=400,
            )
        expression = parse_result.expression

    # --- Load all images with metadata ---
    with connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT i.image_id, i.path, i.thumbnail_path, i.display_path, i.full_path, i.metadata
            FROM images i
            ORDER BY i.path
            """
        ).fetchall()

        # Load person names per image via faces → persons join
        person_rows = conn.execute(
            """
            SELECT f.image_id, p.name
            FROM faces f
            JOIN persons p ON f.person_id = p.person_id
            WHERE f.person_id IS NOT NULL
            """
        ).fetchall()

    # Build image_id → [person_names] map
    persons_by_image: dict[str, list[str]] = {}
    for image_id, name in person_rows:
        persons_by_image.setdefault(image_id, []).append(name)

    # --- Filter ---
    matched: list[dict[str, Any]] = []
    for image_id, path, thumbnail_path, display_path, full_path, metadata_json in rows:
        person_names = persons_by_image.get(image_id, [])
        if expression is not None:
            record: QueryRecord = _build_query_record(image_id, metadata_json, person_names)
            if not evaluate_query(expression, record):
                continue
        matched.append(
            {
                "image_id": image_id,
                "path": path,
                "thumbnail_path": _thumbnail_url(thumbnail_path, db_path),
                "display_path": _thumbnail_url(display_path, db_path),
                "full_path": _thumbnail_url(full_path, db_path),
                "decision": None,
            }
        )

    # --- Paginate ---
    total_count = len(matched)
    page_items = matched[offset : offset + limit]

    return ok(
        {
            "images": page_items,
            "total_count": total_count,
            "query_echo": query,
        }
    )
