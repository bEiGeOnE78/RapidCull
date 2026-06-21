"""FastAPI router for image detail and cull decision endpoints.

All responses use the standard {ok, data|error} envelope from api_envelope.py.
"""

from __future__ import annotations

import json
import mimetypes
import sqlite3
from pathlib import Path
from typing import Any, Literal

from fastapi import APIRouter
from fastapi.responses import FileResponse
from pydantic import BaseModel

from rapidcull.api_envelope import ApiError, ok
from rapidcull.culling import get_decision, set_decision, undo_decision
from rapidcull.galleries import list_image_galleries

router = APIRouter()

_db_path: Path | None = None
_proxy_root: Path | None = None


def configure_router(db_path: Path) -> None:
    """Set the DB path used by all image endpoints."""
    global _db_path, _proxy_root
    _db_path = db_path
    _proxy_root = db_path.parent / "proxies"


def _thumbnail_url(abs_path: str | None) -> str | None:
    """Convert absolute proxy path to /proxies/ URL, or None if unavailable."""
    if not abs_path:
        return None
    if _proxy_root is None:
        return None
    try:
        rel = Path(abs_path).relative_to(_proxy_root)
        return "/proxies/" + str(rel)
    except ValueError:
        return None


def _get_db_path() -> Path:
    if _db_path is None:
        raise RuntimeError("api_images router not configured with a db_path")
    return _db_path


def _require_image(db_path: Path, image_id: str) -> tuple[str, str]:
    """Return (image_id, path) or raise ApiError 404."""
    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            "SELECT image_id, path FROM images WHERE image_id = ?", (image_id,)
        ).fetchone()
    if row is None:
        raise ApiError(
            code="IMAGE_NOT_FOUND",
            message=f"Image '{image_id}' not found.",
            http_status=404,
        )
    return str(row[0]), str(row[1])


@router.get("/api/v1/images/{image_id}")
def get_image(image_id: str) -> dict[str, Any]:
    db_path = _get_db_path()
    _require_image(db_path, image_id)

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        img_row = conn.execute(
            "SELECT image_id, path, thumbnail_path, display_path, full_path, metadata FROM images WHERE image_id = ?",
            (image_id,),
        ).fetchone()
        decision_row = conn.execute(
            "SELECT decision FROM cull_decisions WHERE image_id = ?", (image_id,)
        ).fetchone()
        face_row = conn.execute(
            "SELECT COUNT(*) FROM faces WHERE image_id = ?", (image_id,)
        ).fetchone()

    decision: str | None = decision_row[0] if decision_row else None
    face_count: int = face_row[0] if face_row else 0
    metadata: dict[str, Any] = json.loads(img_row["metadata"]) if img_row["metadata"] else {}

    return ok(
        {
            "image_id": img_row["image_id"],
            "path": img_row["path"],
            "thumbnail_path": _thumbnail_url(img_row["thumbnail_path"]),
            "display_path": _thumbnail_url(img_row["display_path"]),
            "full_path": _thumbnail_url(img_row["full_path"]),
            "metadata": metadata,
            "decision": decision,
            "face_count": face_count,
        }
    )


@router.get("/api/v1/images/{image_id}/decision")
def get_image_decision(image_id: str) -> dict[str, Any]:
    db_path = _get_db_path()
    _require_image(db_path, image_id)

    result = get_decision(db_path, image_id)
    if result is None:
        return ok(None)
    return ok(
        {
            "image_id": result.image_id,
            "decision": result.decision,
            "decided_at": result.decided_at,
        }
    )


class DecisionRequest(BaseModel):
    decision: Literal["pick", "reject"]


@router.post("/api/v1/images/{image_id}/decision")
def post_image_decision(image_id: str, body: DecisionRequest) -> dict[str, Any]:
    db_path = _get_db_path()
    try:
        cull_result = set_decision(db_path, image_id, body.decision)
    except ValueError as exc:
        raise ApiError(
            code="IMAGE_NOT_FOUND",
            message=str(exc),
            http_status=404,
        ) from exc
    return ok({"image_id": cull_result.image_id, "success": cull_result.success})


@router.delete("/api/v1/images/{image_id}/decision")
def delete_image_decision(image_id: str) -> dict[str, Any]:
    db_path = _get_db_path()
    cull_result = undo_decision(db_path, image_id)
    return ok({"image_id": cull_result.image_id, "success": True})


@router.get("/api/v1/images/{image_id}/faces")
def get_image_faces(image_id: str) -> dict[str, Any]:
    """Return face boxes and person assignments for a given image."""
    db_path = _get_db_path()
    _require_image(db_path, image_id)

    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT f.face_id, f.person_id, p.name,
                   f.bbox_x, f.bbox_y, f.bbox_w, f.bbox_h, f.detection_score
            FROM faces f
            LEFT JOIN persons p ON f.person_id = p.person_id
            WHERE f.image_id = ?
            ORDER BY f.face_id
            """,
            (image_id,),
        ).fetchall()

    faces = [
        {
            "face_id": row[0],
            "person_id": row[1],
            "person_name": row[2],
            "bbox": {"x": row[3], "y": row[4], "w": row[5], "h": row[6]},
            "score": row[7],
        }
        for row in rows
    ]
    return ok({"image_id": image_id, "faces": faces})


@router.get("/api/v1/images/{image_id}/galleries")
def get_image_galleries(image_id: str) -> dict[str, Any]:
    """Return all galleries the image belongs to (source-dir + user). Used for trash warning."""
    db_path = _get_db_path()
    _require_image(db_path, image_id)
    galleries = list_image_galleries(db_path, image_id)
    return ok(
        {
            "image_id": image_id,
            "galleries": [
                {
                    "gallery_id": g.gallery_id,
                    "name": g.name,
                    "type": g.type,
                    "count": g.count,
                }
                for g in galleries
            ],
        }
    )


@router.get("/api/v1/images/{image_id}/media")
def get_image_media(image_id: str) -> FileResponse:
    """Stream the original media file for the given image (used for video playback)."""
    db_path = _get_db_path()
    _, path = _require_image(db_path, image_id)
    file_path = Path(path)
    if not file_path.exists():
        raise ApiError(
            code="MEDIA_NOT_FOUND",
            message="Media file not found on disk.",
            http_status=404,
        )
    media_type, _ = mimetypes.guess_type(str(file_path))
    return FileResponse(
        path=file_path,
        media_type=media_type or "application/octet-stream",
        filename=file_path.name,
    )
