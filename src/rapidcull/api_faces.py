"""FastAPI router for face-level endpoints.

POST /api/v1/faces/{face_id}/assign  — assign or unassign a face to/from a person.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter
from pydantic import BaseModel

from rapidcull.api_envelope import ApiError, ok
from rapidcull.schema import connect

router = APIRouter()

_db_path: Optional[Path] = None


def configure_router(db_path: Path) -> None:
    """Set the DB path used by all face endpoints."""
    global _db_path
    _db_path = db_path


def _get_db_path() -> Path:
    if _db_path is None:
        raise RuntimeError("api_faces router not configured with a db_path")
    return _db_path


class AssignFaceRequest(BaseModel):
    person_id: Optional[str] = None


@router.post("/api/v1/faces/{face_id}/assign")
def assign_face(face_id: str, body: AssignFaceRequest) -> dict[str, Any]:
    """Assign or unassign a face to a person.

    Set person_id to a valid person UUID to assign, or null to unassign.
    """
    db_path = _get_db_path()

    with connect(db_path) as conn:
        # Validate face exists.
        face_row = conn.execute(
            "SELECT face_id FROM faces WHERE face_id = ?", (face_id,)
        ).fetchone()
        if face_row is None:
            raise ApiError(
                code="FACE_NOT_FOUND",
                message=f"Face '{face_id}' not found.",
                http_status=404,
            )

        # Validate person exists if provided.
        if body.person_id is not None:
            person_row = conn.execute(
                "SELECT person_id FROM persons WHERE person_id = ?", (body.person_id,)
            ).fetchone()
            if person_row is None:
                raise ApiError(
                    code="PERSON_NOT_FOUND",
                    message=f"Person '{body.person_id}' not found.",
                    http_status=404,
                )

        conn.execute(
            "UPDATE faces SET person_id = ? WHERE face_id = ?",
            (body.person_id, face_id),
        )

    return ok({"ok": True, "face_id": face_id, "person_id": body.person_id})
