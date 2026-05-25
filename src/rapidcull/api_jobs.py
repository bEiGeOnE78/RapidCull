"""FastAPI router for job orchestration endpoints (FR-041).

All responses use the standard {ok, data|error} envelope from api_envelope.py.
Endpoints are mounted under /api/v1/jobs via app.include_router() in api.py.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from rapidcull.api_envelope import ApiError, ok
from rapidcull.jobs import Job, JobNotCancellable, JobProgressEntry, JobState, get_job_store

router = APIRouter()

# ---------------------------------------------------------------------------
# Serialisation helpers
# ---------------------------------------------------------------------------


def _serialize_datetime(dt: datetime) -> str:
    """Serialise a timezone-aware datetime to ISO-8601 with Z suffix."""
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _progress_to_dict(entry: JobProgressEntry) -> dict[str, Any]:
    return {
        "timestamp": _serialize_datetime(entry.timestamp),
        "message": entry.message,
        "percent": entry.percent,
    }


def _job_to_dict(job: Job) -> dict[str, Any]:
    return {
        "job_id": job.job_id,
        "kind": job.kind,
        "params": job.params,
        "state": str(job.state),
        "created_at": _serialize_datetime(job.created_at),
        "updated_at": _serialize_datetime(job.updated_at),
        "result": job.result,
        "error": job.error,
    }


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------


class CreateJobRequest(BaseModel):
    kind: str
    params: dict[str, Any] = {}


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/api/v1/jobs", status_code=201)
def create_job(request: CreateJobRequest) -> JSONResponse:
    """Create a new job in QUEUED state."""
    store = get_job_store()
    job = store.create(kind=request.kind, params=request.params)
    return JSONResponse(status_code=201, content=ok(_job_to_dict(job)))


@router.get("/api/v1/jobs")
def list_jobs(state: str | None = None) -> dict[str, Any]:
    """List all jobs, optionally filtered by state."""
    store = get_job_store()
    filter_state: JobState | None = None
    if state is not None:
        try:
            filter_state = JobState(state)
        except ValueError as exc:
            valid = ", ".join(s.value for s in JobState)
            raise ApiError(
                code="INVALID_STATE_FILTER",
                message=f"'{state}' is not a valid job state. Valid values: {valid}.",
                http_status=400,
            ) from exc
    jobs = store.list_jobs(state=filter_state)
    return ok({"jobs": [_job_to_dict(j) for j in jobs]})


@router.get("/api/v1/jobs/{job_id}")
def get_job(job_id: str) -> dict[str, Any]:
    """Get the full status of a single job."""
    store = get_job_store()
    job = store.get(job_id)
    if job is None:
        raise ApiError(
            code="JOB_NOT_FOUND",
            message=f"Job '{job_id}' not found.",
            http_status=404,
        )
    return ok(_job_to_dict(job))


@router.delete("/api/v1/jobs/{job_id}")
def cancel_job(job_id: str) -> dict[str, Any]:
    """Cancel a job. Returns 404 if not found, 409 if already in a terminal state."""
    store = get_job_store()
    job = store.get(job_id)
    if job is None:
        raise ApiError(
            code="JOB_NOT_FOUND",
            message=f"Job '{job_id}' not found.",
            http_status=404,
        )
    try:
        cancelled_job = store.cancel(job_id)
    except JobNotCancellable as exc:
        raise ApiError(
            code="JOB_NOT_CANCELLABLE",
            message=str(exc),
            http_status=409,
        ) from exc
    return ok(_job_to_dict(cancelled_job))


@router.get("/api/v1/jobs/{job_id}/progress")
def get_job_progress(job_id: str) -> dict[str, Any]:
    """Return all progress entries for a job in append order."""
    store = get_job_store()
    job = store.get(job_id)
    if job is None:
        raise ApiError(
            code="JOB_NOT_FOUND",
            message=f"Job '{job_id}' not found.",
            http_status=404,
        )
    return ok({"entries": [_progress_to_dict(e) for e in job.progress]})
