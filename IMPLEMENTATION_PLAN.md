# Implementation Plan: Job Orchestration (FR-038..041)

**Branch**: `feature/fr-038-job-orchestration`
**Scope**: FR-039 (response envelope), FR-040 (job states), FR-041 (job endpoints)
**Out of scope (deferred to separate branch)**: FR-042 (CLI service lifecycle)
**Already done**: FR-038 (`/api/v1` prefix on existing collection-query endpoint)

## Overview

Add a job-orchestration layer to the RapidCull HTTP API. Introduces a standard `{ok, data|error}`
response envelope, an in-memory Job model with five lifecycle states + guarded transitions, and
five REST endpoints under `/api/v1/jobs` for create / get / list / cancel / progress. No DB, no
auth, no LAN binding. All new code stays mypy-strict and follows the existing frozen-dataclass +
typed module pattern used in `models.py` and `collections.py`.

## Prerequisites

- FR-038 already merged; `/api/v1` prefix in place on `api.py`.
- FastAPI + httpx already in the `[api]` extra (`pyproject.toml`).
- pytest + `fastapi.testclient.TestClient` already wired (see
  `tests/integration/api/test_collection_query_api.py`).
- No new dependencies required.

---

## Stage 1: Response Envelope (FR-039)

**Goal**: Every `/api/v1/*` endpoint returns a uniform success/error envelope, including the
existing collection-query endpoint. Existing tests are updated to match the new shape.

**Success Criteria**:
- Success responses are exactly `{"ok": true, "data": <payload>, "meta": <obj-or-null>}`.
- Error responses are exactly
  `{"ok": false, "error": {"code": "<UPPER_SNAKE>", "message": "<str>", "details": <obj-or-null>}}`.
- A FastAPI exception handler converts `HTTPException` and unhandled `Exception` into the error
  envelope while preserving status codes (400/404/409/500).
- `mypy --strict` and `ruff` clean.
- The existing `test_collection_query_api.py` is updated to assert the new envelope shape and
  still passes.

**Files**:
- New: `src/rapidcull/api_envelope.py` — envelope dataclasses, exception types, FastAPI handlers,
  small `ok(data, meta=None) -> dict` / `err(code, message, details=None, status=400)` helpers.
- Modified: `src/rapidcull/api.py` — wire the exception handlers into `app`; rewrite
  `query_collection` to return `ok(...)` and raise a typed `ApiError` instead of `HTTPException`
  with a free-text detail.
- Modified: `tests/integration/api/test_collection_query_api.py` — assertions now read
  `body["data"]["matching_ids"]` and `body["error"]["code"] == "QUERY_PARSE_ERROR"` /
  `"COLLECTION_NOT_FOUND"`.

**Design notes**:
- Define `class ApiError(Exception)` with `code: str`, `message: str`, `status: int`,
  `details: dict[str, object] | None`. Register a handler that emits the error envelope.
- Also register a handler for FastAPI's `RequestValidationError` -> `code="VALIDATION_ERROR"`,
  status 422, `details` = the pydantic error list.
- Envelope helpers return plain `dict[str, object]` (not pydantic models) so FastAPI's JSON
  encoder serialises them directly and `response_model=` is dropped where it conflicts.

**Tests** (in `tests/integration/api/test_response_envelope.py`, new file):
- Success envelope: `POST .../query` with a valid query returns `ok=true`, `data` contains the
  prior fields, `meta` is present (null is acceptable).
- Parse error envelope: invalid syntax returns `ok=false`, status 400, `error.code` is a stable
  string (e.g. `"QUERY_PARSE_ERROR"`), `error.message` non-empty.
- Not-found envelope: unknown collection id returns 404 and
  `error.code == "COLLECTION_NOT_FOUND"`.
- Validation envelope: posting `{}` (missing `query_text`) returns 422 and
  `error.code == "VALIDATION_ERROR"` with `details` listing the offending field.

**Status**: Complete

---

## Stage 2: Job Model + Endpoints (FR-040 + FR-041)

**Goal**: An in-memory job store with guarded state transitions, exposed via five REST endpoints
that all return the Stage 1 envelope.

**Success Criteria**:
- `JobState` enum with members `QUEUED`, `RUNNING`, `SUCCEEDED`, `FAILED`, `CANCELLED`.
- A pure `transition(current, next) -> bool` function enforces:
  `QUEUED -> RUNNING`, `RUNNING -> {SUCCEEDED, FAILED, CANCELLED}`. All other transitions raise
  `InvalidJobTransition` (subclass of `ApiError`, code `"INVALID_JOB_TRANSITION"`, status 409).
- Terminal states (`SUCCEEDED`, `FAILED`, `CANCELLED`) are sinks; DELETE on a terminal job
  returns 409 with `code="JOB_NOT_CANCELLABLE"`.
- Job ids are stable, sortable strings (ULID-style is overkill — use `f"job_{n:08d}"` from a
  monotonic counter, then sort lex == sort by creation order for deterministic list output).
- `GET /api/v1/jobs` returns jobs sorted by `created_at` ascending (then by id as tiebreak), so
  the same set of created jobs always yields the same array order.
- Progress entries are append-only `(timestamp, message, percent | None)` records stored on the
  job; `GET .../progress` returns them in append order.
- All five endpoints return the Stage 1 envelope. Unknown job id -> 404
  `code="JOB_NOT_FOUND"`.
- `mypy --strict` and `ruff` clean.

**Files**:
- New: `src/rapidcull/jobs.py` — `JobState` (enum.StrEnum), `JobProgressEntry`
  (frozen dataclass), `Job` (frozen dataclass with `state`, `created_at`, `updated_at`,
  `kind`, `params`, `progress`, `result`, `error`), `JobStore` class with thread-safe (use
  `threading.Lock`) `create / get / list / cancel / append_progress / mark_running /
  mark_succeeded / mark_failed` methods, `transition()` helper, and module-level
  `_store: JobStore` singleton accessor `get_job_store()`.
- New: `src/rapidcull/api_jobs.py` — FastAPI `APIRouter` with the five endpoints, pydantic
  request/response models. Router is imported and `app.include_router(router)` in `api.py`.
- Modified: `src/rapidcull/api.py` — include the jobs router; nothing else changes.

**Endpoint contracts** (all responses wrapped in the Stage 1 envelope):

| Method | Path | Request body | Success status | `data` shape |
|---|---|---|---|---|
| POST | `/api/v1/jobs` | `{"kind": str, "params": object}` | 201 | full job object |
| GET | `/api/v1/jobs/{job_id}` | — | 200 | full job object |
| GET | `/api/v1/jobs` | — (query: `?state=` optional) | 200 | `{"jobs": [job, ...]}` |
| DELETE | `/api/v1/jobs/{job_id}` | — | 200 | full job object (state=CANCELLED) |
| GET | `/api/v1/jobs/{job_id}/progress` | — | 200 | `{"entries": [progress, ...]}` |

Job object shape:
```json
{
  "job_id": "job_00000001",
  "kind": "ingest",
  "state": "queued",
  "params": { "...": "..." },
  "created_at": "2026-05-24T12:00:00Z",
  "updated_at": "2026-05-24T12:00:00Z",
  "result": null,
  "error": null
}
```

Progress entry shape:
```json
{ "timestamp": "2026-05-24T12:00:01Z", "message": "stage 1", "percent": 12.5 }
```

**Design notes**:
- No worker execution yet — POST creates the job in `QUEUED`; the runner is a later concern. To
  avoid the store feeling vestigial, expose `mark_running` / `mark_succeeded` / etc. on
  `JobStore` so future code (and tests) can drive transitions without exposing a separate API.
- Timestamps: `datetime.now(tz=timezone.utc)`, serialised as ISO-8601 with `Z` suffix.
- `params` is `dict[str, object]` (no schema yet — kinds will validate their own params later).
- Concurrency: a single `threading.Lock` inside `JobStore` is sufficient given the in-process
  model; document that this is single-process only.
- Determinism for `list`: sort by `(created_at, job_id)`, both monotonically increasing, so
  insertion order == sort order. Optional `?state=queued` filter applied after sort.

**Tests** (under `tests/integration/api/`):
- `test_jobs_state_machine.py` — pure unit tests on `transition()` covering all 25
  state-pair combinations: legal ones return new state, illegal ones raise
  `InvalidJobTransition`. Also covers `JobStore.cancel` rejecting terminal jobs with the right
  code/status.
- `test_jobs_endpoints.py` —
  - Create job: POST returns 201, envelope ok=true, state == "queued", id starts with `job_`.
  - Get unknown: 404, `code="JOB_NOT_FOUND"`.
  - List determinism: create 3 jobs in order A,B,C — list returns ids in `[A,B,C]` order on
    repeated calls.
  - List filter: `?state=queued` returns only queued jobs.
  - Cancel queued: DELETE returns 200, state == "cancelled".
  - Cancel running: drive job to RUNNING via store, DELETE returns 200, state == "cancelled".
  - Cancel terminal: drive to SUCCEEDED via store, DELETE returns 409,
    `code="JOB_NOT_CANCELLABLE"`.
  - Progress: append two entries via store, `GET .../progress` returns them in append order
    with all three fields.
- Each test uses an `autouse` fixture that resets the in-memory store between tests (same
  pattern as the existing `_collections` registry teardown).

**Status**: Complete

---

## Stage 3: Test Hardening + CI Wiring

**Goal**: Cross-stage smoke coverage, lint/type gates green, and a documented manual smoke
script. Catches regressions where Stage 1 envelope assumptions leak into Stage 2 handlers.

**Success Criteria**:
- One end-to-end test exercises the full happy path: create job -> get job -> append progress
  via store -> mark running -> mark succeeded -> get job (terminal) -> list shows it -> cancel
  returns 409.
- One negative end-to-end test exercises envelope consistency: create with malformed body, get
  unknown id, cancel terminal — all three responses have identical envelope structure (same
  keys, same nesting) verified by a shared assertion helper.
- `pytest -q` passes; `mypy --strict src/rapidcull` passes; `ruff check src tests` passes.
- README or a short `docs/api.md` snippet (only if `docs/` already exists — otherwise skip
  docs) lists the five endpoints and the envelope shape.

**Files**:
- New: `tests/integration/api/test_jobs_end_to_end.py` — the two end-to-end tests above, plus
  a `_assert_envelope_shape(body, *, ok: bool)` helper.
- Modified (only if needed to make mypy strict pass): `src/rapidcull/jobs.py`,
  `src/rapidcull/api_jobs.py`, `src/rapidcull/api_envelope.py`.
- Optional, only if `docs/` exists already: `docs/api.md` snippet.

**Tests**:
- Happy path E2E (see above).
- Envelope consistency E2E (see above).
- Re-run full suite to confirm Stage 1's edit to `test_collection_query_api.py` still passes
  alongside the new tests.

**Status**: Complete

---

## Edge Cases to Handle

- Concurrent POST /jobs from two TestClient threads — the `JobStore` lock must serialise id
  allocation so no two jobs share an id.
- DELETE on a job that was just transitioned to a terminal state between the lookup and the
  cancel call — `JobStore.cancel` must perform the read+transition under the lock, not in the
  handler.
- `?state=` filter with an unknown value — return 400 `code="INVALID_STATE_FILTER"` rather
  than silently returning everything.
- Empty progress list — `GET .../progress` returns `{"entries": []}`, not 404.
- Pydantic `RequestValidationError` for a missing `kind` on POST /jobs must come back through
  the Stage 1 handler as `code="VALIDATION_ERROR"`, status 422.
- Datetime serialisation: ensure ISO-8601 with explicit `Z` (or `+00:00`) — pick one and stick
  to it; tests assert the chosen format.

## Verification

- [ ] `pytest -q` — all tests pass.
- [ ] `mypy --strict src/rapidcull` — clean.
- [ ] `ruff check src tests` — clean.
- [ ] `black --check src tests` — clean.
- [ ] Manual: `uvicorn rapidcull.api:app` then `curl -s localhost:8000/api/v1/jobs | jq` shows
  the envelope shape with an empty `data.jobs` array.
- [ ] Existing `test_collection_query_api.py` updated to the new envelope and green.
- [ ] No new runtime dependencies added to `pyproject.toml`.
- [ ] FR-042 explicitly NOT touched in this branch.
