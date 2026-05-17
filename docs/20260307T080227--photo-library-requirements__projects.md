# Photo Library Requirements (Validated + Refined)

Generated: 2026-03-07T08:02:27  
Revised: 2026-03-07T08:15:00

## 1) Purpose

This project is a **Linux-first, local-first** photo management toolkit for large libraries. It shall provide an end-to-end workflow for ingest, metadata indexing, proxy generation, gallery creation, culling, and face-recognition-assisted organization.

## 2) Product Decisions Captured

- Deployment modes: **localhost-only and LAN mode** (switchable)
- Auth: **No auth in localhost mode; token/password required in LAN mode**
- API contracts: **Versioned + standardized schema**
- Long-running operations: **job model with lifecycle states**
- Consistency policy: **DB canonical metadata; JSON UI state/cache; filesystem media truth**
- Deletion policy: **trash-first soft delete + explicit hard delete path**
- Face privacy: **user-controlled retention and deletion**
- Performance priority: **aggressive UI speed targets**
- Parallelism: **adaptive parallelism with user-configurable cap**
- Platform: **Linux only** (macOS requirements removed)

---

## 3) Functional Requirements (Testable)

### 3.1 Ingestion, Metadata, and Indexing

FR-001. System shall initialize SQLite schema on first run and verify schema version on startup.

FR-002. System shall scan configured library roots and ingest supported image/video formats.

FR-002a. System shall extract technical/media metadata using ExifTool for supported assets during ingest.

FR-002b. Metadata extraction shall support ExifTool persistent batch mode (`-stay_open`) so a single process can serve multiple asset requests in one ingest run.

FR-002c. Batch-mode metadata responses shall be deterministically mapped to input assets and normalized into canonical fields used by DB, JSON exports, and API responses.

FR-002d. If ExifTool is unavailable, returns malformed output, or fails during batch execution, ingest shall continue-on-error with per-item failure reasons and final summary accounting.

FR-003. System shall support incremental processing by file fingerprint (`path + mtime + size` minimum) and support force-reprocess mode.

FR-004. Every media asset shall have a stable internal `image_id` used across DB, JSON exports, and API responses.

FR-005. Failed ingest items shall be recorded with reason and surfaced in run summary.

### 3.2 Proxy and Derivative Generation

FR-006. System shall generate thumbnails for all supported still images.

FR-006a. Still-image proxy/thumbnail generation shall use ImageMagick as the primary conversion backend with deterministic output settings.

FR-007. System shall generate HEIC display proxies where native browser support is unavailable.

FR-007a. HEIC display proxy generation shall validate ImageMagick HEIF capability before processing and return actionable setup errors when unavailable.

FR-008. System shall generate RAW JPG proxies via RawTherapee pipeline.

FR-008a. RAW display proxy generation shall use RawTherapee CLI with project-defined processing profile/preset contract.

FR-008b. RAW/ImageMagick tool failures shall not abort full runs by default; failures shall be recorded per asset with actionable reason codes.

FR-009. System shall generate video proxies (H.264 MP4 baseline profile or project-selected equivalent).

FR-010. System shall support per-asset regeneration (selected IDs) and bulk regeneration.

FR-011. System shall provide orphan cleanup for stale thumbnail/proxy artifacts and produce a deletion report.

### 3.3 Gallery Lifecycle

FR-012. System shall create virtual galleries via hard links without modifying original masters.

FR-013. System shall support gallery creation from: metadata queries, picks, and face sample sets.

FR-014. System shall rebuild gallery JSON metadata for one gallery or all galleries.

FR-015. System shall maintain a single galleries index file consumed by UI/API.

FR-015a. Index rebuild shall be deterministic (stable ordering and idempotent output for unchanged inputs).

FR-015b. Rebuild shall continue when individual gallery metadata is unreadable or invalid, skipping failed entries and recording per-gallery errors.

FR-015c. If no valid galleries are discovered, system shall still write a valid empty index artifact.

FR-015d. Rebuild result shall include summary counts (processed/skipped/failed) and error details sufficient for operator remediation.

FR-016. Gallery rename/delete operations shall enforce path allowlist checks and reject out-of-scope paths.

### 3.4 Query Language (Explicit Grammar)

FR-017. System shall support a structured query grammar (not free-form NLP).

FR-018. Supported fields shall include at minimum: `person`, `date`, `camera`, `lens`, `iso`, `fnumber`, `focal`, `keyword`.

FR-019. Supported operators shall include `=`, `!=`, `>`, `>=`, `<`, `<=`, and `~` (contains) where type-appropriate.

FR-020. Boolean logic shall support `AND`, `OR`, `NOT`, and parentheses.

FR-021. Invalid queries shall return actionable validation errors (unknown field/operator, malformed value, bad date).

FR-022. Query behavior shall be documented with examples and expected results.

### 3.5 Face Recognition and Person Management

FR-023. System shall detect faces and store embeddings for supported assets.

FR-024. System shall cluster faces with configurable parameters (e.g., distance threshold / min samples).

FR-025. System shall support naming, renaming, merging, and deleting person identities.

FR-026. System shall expose image-level face boxes + person labels for UI overlay rendering.

FR-027. System shall support re-cluster-all and new-faces-only clustering modes.

FR-028. System shall support deletion of person data and associated embeddings per retention settings.

### 3.6 Culling and Deletion Flows

FR-029. System shall persist picks/rejects with `image_id` references.

FR-030. System shall restore picks/rejects across sessions.

FR-031. Deletion flow shall be trash-first by default with preview and confirmation.

FR-032. Hard delete shall require explicit user action and shall produce an auditable operation summary.

### 3.7 UI and Interaction

FR-033. UI shall provide thumbnail grid, full-screen single view, metadata sidebar, and gallery selector.

FR-034. UI shall support keyboard-first workflow (navigation, pick/reject, command palette).

FR-035. UI shall support touch interactions for primary browsing/culling operations.

FR-036. UI shall display long-running operation status with timestamped progress entries.

FR-037. UI shall provide sorting and fast context switching without full-page reload.

### 3.8 API and Job Orchestration

FR-038. APIs shall be versioned under `/api/v1`.

FR-039. APIs shall use a standard response envelope:
- success: `{ "ok": true, "data": ..., "meta": ... }`
- error: `{ "ok": false, "error": { "code": "...", "message": "...", "details": ... } }`

FR-040. Long-running operations shall be modeled as jobs with states: `queued`, `running`, `succeeded`, `failed`, `cancelled`.

FR-041. Job endpoints shall support create/status/list/cancel and progress retrieval.

FR-042. CLI shall expose start/stop/restart for services and a unified "process new" pipeline.

### 3.9 Security, Access, and Mode Controls

FR-043. In localhost mode, auth may be disabled by default.

FR-044. In LAN mode, all mutating endpoints shall require token/password authentication.

FR-045. CORS policy shall be explicit and restrictive in LAN mode (no wildcard origins).

FR-046. All file/path inputs shall be normalized and validated before use.

FR-046a. External tool invocations (ExifTool/ImageMagick/RawTherapee) shall use argument-safe process execution (no shell interpolation of user-provided values) and validated normalized paths only.

### 3.10 Backup, Recovery, and Data Consistency

FR-047. System shall provide backup and restore commands covering DB + JSON state + galleries index.

FR-048. System shall provide consistency check/reconciliation command to detect and repair DB/JSON/FS drift.

FR-049. System shall provide schema migration path with explicit migration versions.

FR-050. Run summaries shall include processed, skipped, failed counts and elapsed time.

FR-050a. Run summaries shall include per-tool processing/failure counts and reason taxonomy for metadata/proxy pipelines.

---

## 4) Non-Functional Requirements (NFR)

### 4.1 Performance and UX Speed (High Priority)

NFR-001. Gallery open time (cached metadata) shall be **< 1.5s p95** for target dataset/profile.

NFR-002. Single-image next/prev switch shall be **< 100ms perceived p95** when adjacent preloading is available.

NFR-003. Command response latency (UI action to visible feedback) shall be **< 50ms p95** for non-IO operations.

NFR-004. Background work shall not block core UI navigation and marking operations.

### 4.2 Parallel Processing

NFR-005. Pipeline operations shall use adaptive parallelism (default workers = `min(cpu_count-1, configured_cap)` with floor 1).

NFR-006. User shall be able to set a max parallel worker cap.

NFR-007. Parallel operations shall provide deterministic completion accounting and per-item error reporting.

### 4.3 Reliability and Failure Behavior

NFR-008. Processing pipelines shall continue-on-error by default and emit final failure summary.

NFR-009. Job state transitions shall be durable across process restarts where feasible.

NFR-010. Health/status endpoint shall report service readiness and key dependency state.

### 4.4 Observability

NFR-011. Logs shall be structured (timestamp, level, component, message, context fields).

NFR-012. Each job/run shall emit a unique correlation ID used across logs/events.

NFR-013. System shall expose summary metrics for ingest/proxy/face operations (counts + duration).

### 4.5 Privacy and Safety

NFR-014. Face embeddings/person records shall be removable by user action within a single operation flow.

NFR-015. Destructive operations shall require explicit confirmation and produce audit-friendly summaries.

### 4.6 External Tooling Reliability and Performance

NFR-016. Metadata extraction for ingest runs shall use ExifTool persistent batch mode by default (with documented fallback mode) to minimize process startup overhead.

NFR-017. If persistent ExifTool mode fails mid-run, system shall attempt bounded restart/retry and preserve deterministic accounting for processed/skipped/failed items.

NFR-018. External tool preflight checks shall provide actionable diagnostics for missing/incompatible ExifTool, ImageMagick (HEIF), and RawTherapee dependencies before relevant pipeline phases execute.

---

## 5) Query Grammar v1 (Baseline)

### 5.1 Syntax Examples

- `person:alice AND date>=2024-01-01`
- `(person:alice OR person:bob) AND iso>800`
- `camera~"Leica" AND NOT keyword:"blurred"`

### 5.2 Validation Requirements

- Unknown field → error with suggestion
- Unsupported operator for field type → error with allowed operators
- Invalid date/value format → error with expected format

---

## 6) Scope and Constraints

- Platform support is **Linux only** for this requirements baseline.
- Local/self-hosted deployment is primary; cloud multi-tenant behavior is out of scope.
- Existing placeholder endpoints are in scope for hardening under standardized API/job model.
