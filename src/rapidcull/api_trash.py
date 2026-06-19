"""FastAPI router for trash and restore endpoints.

All responses use the standard {ok, data|error} envelope from api_envelope.py.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter

from rapidcull.api_envelope import ApiError, ok
from rapidcull.culling import list_trash, restore_from_trash

router = APIRouter()

_db_path: Path | None = None


def configure_router(db_path: Path) -> None:
    """Set the DB path used by all trash endpoints."""
    global _db_path
    _db_path = db_path


def _get_db_path() -> Path:
    if _db_path is None:
        raise RuntimeError("api_trash router not configured with a db_path")
    return _db_path


def _get_trash_dir(db_path: Path) -> Path:
    """Derive the trash directory from the DB path."""
    return db_path.parent / ".trash"


@router.get("/api/v1/trash")
def get_trash() -> dict[str, Any]:
    db_path = _get_db_path()
    entries = list_trash(db_path)
    items = [
        {
            "image_id": e.image_id,
            "original_path": e.original_path,
            "trashed_at": e.trashed_at,
        }
        for e in entries
    ]
    return ok({"items": items, "count": len(items)})


@router.post("/api/v1/trash/{image_id}/restore")
def post_restore(image_id: str) -> dict[str, Any]:
    db_path = _get_db_path()
    trash_dir = _get_trash_dir(db_path)
    result = restore_from_trash(db_path, image_id, trash_dir)
    if not result.success:
        raise ApiError(
            code="TRASH_RESTORE_FAILED",
            message=result.reason or f"Could not restore '{image_id}' from trash.",
            http_status=404,
        )
    return ok({"image_id": result.image_id, "success": True})
