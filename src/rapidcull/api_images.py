"""FastAPI router for image detail and cull decision endpoints.

All responses use the standard {ok, data|error} envelope from api_envelope.py.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Literal

from fastapi import APIRouter
from pydantic import BaseModel

from rapidcull.api_envelope import ApiError, ok
from rapidcull.culling import get_decision, set_decision, undo_decision

router = APIRouter()

_db_path: Path | None = None


def configure_router(db_path: Path) -> None:
    """Set the DB path used by all image endpoints."""
    global _db_path
    _db_path = db_path


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
    img_id, path = _require_image(db_path, image_id)

    with sqlite3.connect(db_path) as conn:
        decision_row = conn.execute(
            "SELECT decision FROM cull_decisions WHERE image_id = ?", (image_id,)
        ).fetchone()
        face_row = conn.execute(
            "SELECT COUNT(*) FROM faces WHERE image_id = ?", (image_id,)
        ).fetchone()

    decision: str | None = decision_row[0] if decision_row else None
    face_count: int = face_row[0] if face_row else 0

    return ok(
        {
            "image_id": img_id,
            "path": path,
            "metadata": {},
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
