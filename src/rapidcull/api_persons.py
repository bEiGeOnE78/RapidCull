"""FastAPI router for person CRUD endpoints.

All responses use the standard {ok, data|error} envelope from api_envelope.py.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter
from fastapi.responses import FileResponse
from pydantic import BaseModel

from rapidcull.api_envelope import ApiError, ok
from rapidcull.persons import delete_person, list_persons, merge_persons, rename_person

router = APIRouter()

_db_path: Optional[Path] = None
_library_root: Optional[Path] = None


def configure_router(db_path: Path, library_root: Optional[Path] = None) -> None:
    """Set the DB path (and optional library root) used by all person endpoints."""
    global _db_path, _library_root
    _db_path = db_path
    _library_root = library_root


def _get_db_path() -> Path:
    if _db_path is None:
        raise RuntimeError("api_persons router not configured with a db_path")
    return _db_path


def _require_person(db_path: Path, person_id: str) -> None:
    """Raise ApiError 404 if person does not exist."""
    with sqlite3.connect(db_path) as conn:
        row = conn.execute("SELECT 1 FROM persons WHERE person_id = ?", (person_id,)).fetchone()
    if row is None:
        raise ApiError(
            code="PERSON_NOT_FOUND",
            message=f"Person '{person_id}' not found.",
            http_status=404,
        )


@router.get("/api/v1/persons")
def get_persons() -> dict[str, Any]:
    db_path = _get_db_path()
    persons = list_persons(db_path)
    with sqlite3.connect(db_path) as conn:
        face_counts: dict[str, int] = {}
        for row in conn.execute(
            "SELECT person_id, COUNT(*) FROM faces WHERE person_id IS NOT NULL GROUP BY person_id"
        ).fetchall():
            face_counts[row[0]] = row[1]

    return ok(
        {
            "persons": [
                {
                    "person_id": p.person_id,
                    "name": p.name,
                    "created_at": p.created_at,
                    "face_count": face_counts.get(p.person_id, 0),
                }
                for p in persons
            ]
        }
    )


class RenamePersonRequest(BaseModel):
    name: str


@router.patch("/api/v1/persons/{person_id}")
def patch_person(person_id: str, body: RenamePersonRequest) -> dict[str, Any]:
    db_path = _get_db_path()
    try:
        updated = rename_person(db_path, person_id, body.name)
    except ValueError as exc:
        raise ApiError(
            code="PERSON_NOT_FOUND",
            message=str(exc),
            http_status=404,
        ) from exc
    return ok({"person_id": updated.person_id, "name": updated.name})


class MergePersonRequest(BaseModel):
    into_person_id: str


@router.post("/api/v1/persons/{person_id}/merge")
def merge_person(person_id: str, body: MergePersonRequest) -> dict[str, Any]:
    db_path = _get_db_path()
    try:
        result = merge_persons(db_path, person_id, body.into_person_id)
    except ValueError as exc:
        raise ApiError(
            code="PERSON_NOT_FOUND",
            message=str(exc),
            http_status=404,
        ) from exc
    return ok(
        {
            "reassigned_count": result.reassigned_count,
            "deleted_person_id": result.deleted_person_id,
        }
    )


@router.delete("/api/v1/persons/{person_id}")
def delete_person_endpoint(person_id: str) -> dict[str, Any]:
    db_path = _get_db_path()
    # Check existence and collect counts before deletion
    _require_person(db_path, person_id)
    with sqlite3.connect(db_path) as conn:
        deleted_face_count: int = conn.execute(
            "SELECT COUNT(*) FROM faces WHERE person_id = ?", (person_id,)
        ).fetchone()[0]
    try:
        # unlink faces (don't delete embeddings)
        delete_person(db_path, person_id, delete_embeddings=False)
    except ValueError as exc:
        raise ApiError(
            code="PERSON_NOT_FOUND",
            message=str(exc),
            http_status=404,
        ) from exc
    return ok(
        {
            "deleted_person_id": person_id,
            "deleted_face_count": deleted_face_count,
            "unlinked_face_count": deleted_face_count,
        }
    )


@router.get("/api/v1/persons/{person_id}/thumbnail")
def get_person_thumbnail(person_id: str) -> FileResponse:
    """Return a 96×96 WebP face crop for the best-scoring face of person_id."""
    from rapidcull.face_thumbnails import render_person_thumbnail  # noqa: PLC0415

    db_path = _get_db_path()
    _require_person(db_path, person_id)

    lib_root = _library_root if _library_root is not None else db_path.parent
    thumb_path = render_person_thumbnail(db_path, person_id, lib_root)
    if thumb_path is None:
        raise ApiError(
            code="NO_FACES",
            message=f"Person '{person_id}' has no faces.",
            http_status=404,
        )
    return FileResponse(str(thumb_path), media_type="image/webp")
