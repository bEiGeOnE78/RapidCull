# Implementation Plan: Security Baseline (FR-043–046)

**Branch**: `feature/fr-043-security-baseline`
**Scope**: FR-043 (localhost auth off), FR-044 (LAN mutating auth), FR-045 (CORS), FR-046/046a (path validation)

## Stage 1: Mode-aware CORS (FR-045)

**Goal**: CORSMiddleware wired into FastAPI app with env-var-driven origin config

**Success Criteria**:
- `RAPIDCULL_MODE=localhost` (default): allows `http://localhost`, `http://127.0.0.1`
- `RAPIDCULL_MODE=lan` + `RAPIDCULL_ALLOWED_ORIGINS=...`: uses explicit origin list, no wildcard
- `src/rapidcull/security.py` contains `Settings` dataclass + `get_settings()` + `configure_cors(app)`
- Integration tests verify CORS response headers in both modes

**Tests**: `tests/integration/api/test_security_cors.py`

**Status**: Not Started

---

## Stage 2: Mode-aware auth middleware (FR-043/044)

**Goal**: Mutating endpoints (POST/PUT/PATCH/DELETE) reject unauthenticated requests in LAN mode

**Success Criteria**:
- `RAPIDCULL_MODE=localhost`: no auth required on any endpoint
- `RAPIDCULL_MODE=lan` + `RAPIDCULL_AUTH_TOKEN=<tok>`: mutating endpoints require `Authorization: Bearer <tok>`
- Missing/wrong token → 401 with JSON body `{"detail": "Unauthorized"}`
- Read-only endpoints (GET) never require auth
- Implemented as Starlette middleware (not per-route dependency)

**Tests**: `tests/integration/api/test_security_auth.py`

**Status**: Not Started

---

## Stage 3: Path normalization utility (FR-046/046a)

**Goal**: `normalize_path()` utility rejects traversal attempts; wired into CLI process-new

**Success Criteria**:
- `normalize_path(path)` returns resolved `Path`
- `normalize_path(path, base_dir=X)` raises `ValueError` if resolved path not inside `X`
- Path traversal strings (`../../etc/passwd`) rejected when base_dir provided
- CLI `process-new --source-dir` uses `normalize_path` (replaces ad-hoc check)
- ExifTool adapter verified: uses list args, no `shell=True`

**Tests**: `tests/unit/test_path_utils.py`

**Status**: Not Started

---

## Stage 4: Quality gates

**Goal**: All gates green
**Success Criteria**: `black`, `ruff`, `mypy --strict src/rapidcull`, `pytest` all pass
**Status**: Not Started
