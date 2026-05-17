# Photo Library Acceptance Test Matrix

Generated: 2026-03-07T08:18:00  
Source Requirements: `20260307T080227--photo-library-requirements__projects.md`

## 1) How to Use This Matrix

- This matrix provides **pass/fail acceptance checks** for each FR/NFR.
- Tests are grouped for **parallel execution** by domain: Ingest, Proxies, Galleries, Query, Face, UI, API/Jobs, Security, Backup/Consistency, NFR.
- Each test includes: method, scenario type (Happy/Edge/Error), and expected result.

## 2) Parallel Execution Batches

### Batch A (can run in parallel)
- Ingestion/metadata tests (FR-001..005)
- Query grammar tests (FR-017..022)
- Security/auth mode tests (FR-043..046)

### Batch B (depends on A indexed data)
- Proxy generation tests (FR-006..011)
- Face tests (FR-023..028)
- Gallery tests (FR-012..016)

### Batch C (depends on A+B)
- UI interaction tests (FR-033..037)
- API/job orchestration tests (FR-038..042)
- Backup/reconciliation tests (FR-047..050)

### Batch D (cross-cutting NFR validation)
- Performance, parallelism, reliability, observability, privacy/safety (NFR-001..015)

---

## 3) Functional Requirement Acceptance Tests

## 3.1 Ingestion, Metadata, and Indexing

### FR-001
- **Test**: Fresh install startup initializes schema; subsequent startup verifies schema version.
- **Method**: Integration (CLI/API startup)
- **Scenarios**: Happy + Error (corrupt schema version)
- **Pass Criteria**: DB created on first run; mismatch yields actionable migration error.

### FR-002
- **Test**: Scan configured root with mixed supported/unsupported files using ExifTool-backed metadata extraction in persistent batch mode.
- **Method**: Integration + tool invocation contract checks
- **Scenarios**: Happy + Edge + Error
  - Happy: one ExifTool process serves multiple assets in a run and metadata maps correctly per file
  - Edge: nested dirs/symlinks and missing optional EXIF tags still produce valid normalized metadata
  - Error: ExifTool missing/malformed output/process interruption triggers continue-on-error with per-item reasons
- **Pass Criteria**: Supported media ingested; deterministic metadata mapping/normalization is preserved; unsupported media skipped with reason; failure accounting is complete.

### FR-003
- **Test**: Re-run ingest without changes, then with touched metadata and force mode.
- **Method**: Integration
- **Scenarios**: Happy + Edge
- **Pass Criteria**: Unchanged files skipped; changed files reprocessed; force mode reprocesses all selected.

### FR-004
- **Test**: Verify stable `image_id` across DB rows, JSON exports, and API payloads.
- **Method**: Contract + Integration
- **Scenarios**: Happy + Edge (renamed files)
- **Pass Criteria**: IDs remain stable; no duplicate ID assignment.

### FR-005
- **Test**: Introduce unreadable/corrupt files during ingest.
- **Method**: Integration
- **Scenarios**: Error
- **Pass Criteria**: Failures recorded with reason; final run summary includes failed count.

## 3.2 Proxy and Derivative Generation

### FR-006
- **Test**: Generate thumbnails for representative still image set.
- **Method**: Integration
- **Scenarios**: Happy + Edge (very large images)
- **Pass Criteria**: Thumbnail exists and is displayable for each eligible still image; generation uses ImageMagick deterministic settings for unchanged inputs.

### FR-007
- **Test**: HEIC inputs produce browser-compatible display proxies where needed.
- **Method**: Integration + UI smoke
- **Scenarios**: Happy + Edge + Error (missing HEIF capability)
- **Pass Criteria**: HEIC images render in UI using generated proxy path; missing HEIF capability returns actionable setup diagnostics.

### FR-008
- **Test**: RAW inputs produce JPG proxies through configured pipeline.
- **Method**: Integration
- **Scenarios**: Happy + Error (tool missing/preset invalid)
- **Pass Criteria**: RAW proxy generated through RawTherapee CLI profile contract; tool/preset failures are recorded per item without halting full batch.

### FR-009
- **Test**: Video inputs produce playable proxy outputs.
- **Method**: Integration + UI smoke
- **Scenarios**: Happy + Edge (long/high-bitrate source)
- **Pass Criteria**: Proxy playable in browser without decode failure.

### FR-010
- **Test**: Regenerate selected IDs and bulk selection.
- **Method**: Integration
- **Scenarios**: Happy + Error (invalid ID)
- **Pass Criteria**: Only selected assets regenerated; invalid IDs reported without halting all work.

### FR-011
- **Test**: Create stale proxy artifacts then run orphan cleanup.
- **Method**: Integration
- **Scenarios**: Happy + Edge (large orphan set)
- **Pass Criteria**: Orphans removed; cleanup report includes counts and paths.

## 3.3 Gallery Lifecycle

### FR-012
- **Test**: Create gallery from query and inspect link type.
- **Method**: Integration + filesystem verification
- **Scenarios**: Happy
- **Pass Criteria**: Hard links created; original masters unmodified.

### FR-013
- **Test**: Create galleries by query, picks, and face sample modes.
- **Method**: Integration
- **Scenarios**: Happy + Edge (empty result set)
- **Pass Criteria**: Each mode works; empty result produces valid empty gallery with message.

### FR-014
- **Test**: Rebuild one gallery metadata then rebuild all.
- **Method**: Integration
- **Scenarios**: Happy + Error (missing gallery path)
- **Pass Criteria**: JSON regenerated correctly; missing path returns explicit error.

### FR-015
- **Test**: Rebuild central galleries index across mixed gallery metadata states.
- **Method**: Integration + API contract
- **Scenarios**: Happy + Edge + Error
  - Happy: all gallery metadata valid
  - Edge: zero galleries present
  - Error: one or more gallery metadata files missing/corrupt/unreadable
- **Pass Criteria**:
  - Deterministic index ordering and stable output for unchanged inputs
  - Empty valid index produced when no galleries exist
  - Invalid galleries skipped without aborting full rebuild
  - Rebuild summary reports processed/skipped/failed counts and per-gallery failure reasons

### FR-016
- **Test**: Attempt rename/delete with in-scope and out-of-scope paths.
- **Method**: Security integration
- **Scenarios**: Happy + Error (path traversal)
- **Pass Criteria**: Allowed paths succeed; traversal/out-of-scope requests are rejected.

## 3.4 Query Language

### FR-017
- **Test**: Execute grammar-based queries (no NLP free text assumptions).
- **Method**: Parser + integration tests
- **Scenarios**: Happy
- **Pass Criteria**: Valid grammar parses and returns deterministic results.

### FR-018
- **Test**: Field coverage test for required fields.
- **Method**: Parser/contract
- **Scenarios**: Happy + Error (unknown field)
- **Pass Criteria**: Required fields accepted; unknown fields rejected with suggestions.

### FR-019
- **Test**: Operator matrix by field type.
- **Method**: Parser + integration
- **Scenarios**: Happy + Error
- **Pass Criteria**: Supported operators work; unsupported operator/field combinations fail cleanly.

### FR-020
- **Test**: Boolean precedence and parentheses correctness.
- **Method**: Unit + integration
- **Scenarios**: Happy + Edge
- **Pass Criteria**: Result sets match expected truth table outcomes.

### FR-021
- **Test**: malformed queries (bad date, bad token, mismatched parentheses).
- **Method**: Parser
- **Scenarios**: Error
- **Pass Criteria**: Actionable error includes exact issue and expected format.

### FR-022
- **Test**: Validate docs examples execute as advertised.
- **Method**: Documentation test / smoke script
- **Scenarios**: Happy
- **Pass Criteria**: All documented examples parse and return expected class of results.

## 3.5 Face Recognition and Person Management

### FR-023
- **Test**: Run detection + embedding extraction on sample set.
- **Method**: Integration
- **Scenarios**: Happy + Error (model unavailable)
- **Pass Criteria**: Embeddings stored for detectable faces; missing model yields actionable setup error.

### FR-024
- **Test**: Cluster with configurable params across known dataset.
- **Method**: Integration + quality check
- **Scenarios**: Happy + Edge (sparse faces)
- **Pass Criteria**: Clusters created; parameter changes affect cluster granularity as expected.

### FR-025
- **Test**: Name, rename, merge, delete person identities.
- **Method**: Integration/API
- **Scenarios**: Happy + Error (merge conflicts)
- **Pass Criteria**: Identity operations persist correctly and are reflected in overlays/search.

### FR-026
- **Test**: Retrieve overlays in UI for labeled/unlabeled faces.
- **Method**: UI integration
- **Scenarios**: Happy
- **Pass Criteria**: Bounding boxes and labels render correctly by image.

### FR-027
- **Test**: Compare re-cluster-all vs new-faces-only outcomes.
- **Method**: Integration
- **Scenarios**: Happy
- **Pass Criteria**: Mode behavior matches definition and does not regress existing labels unexpectedly.

### FR-028
- **Test**: Delete person + embeddings via retention flow.
- **Method**: Integration + privacy audit
- **Scenarios**: Happy + Error (non-existent person)
- **Pass Criteria**: Data removed from DB and no longer visible in UI/API.

## 3.6 Culling and Deletion

### FR-029
- **Test**: Mark picks/rejects and verify persistence format with `image_id`.
- **Method**: UI + storage integration
- **Scenarios**: Happy
- **Pass Criteria**: State persists and references valid IDs only.

### FR-030
- **Test**: Restart app and verify state restoration.
- **Method**: Integration
- **Scenarios**: Happy
- **Pass Criteria**: Picks/rejects restored without duplication.

### FR-031
- **Test**: Execute default delete flow and inspect trash destination.
- **Method**: Integration
- **Scenarios**: Happy + Edge (name collisions in trash)
- **Pass Criteria**: Files moved to trash, not hard-deleted, after preview + confirmation.

### FR-032
- **Test**: Trigger explicit hard delete and inspect operation summary.
- **Method**: Integration + audit
- **Scenarios**: Happy + Error (permission denied)
- **Pass Criteria**: Hard delete only on explicit action; summary includes successes/failures.

## 3.7 UI and Interaction

### FR-033
- **Test**: Render core UI regions with representative dataset.
- **Method**: UI smoke/integration
- **Scenarios**: Happy
- **Pass Criteria**: Thumbnail grid, full-screen, sidebar, gallery selector all available and interactive.

### FR-034
- **Test**: Keyboard navigation and command palette actions.
- **Method**: UI integration
- **Scenarios**: Happy + Error (invalid command)
- **Pass Criteria**: Key actions execute with visible feedback and no navigation lockup.

### FR-035
- **Test**: Touch gestures and toolbar actions for browse/cull.
- **Method**: UI integration (touch emulation/device)
- **Scenarios**: Happy
- **Pass Criteria**: Core browse + cull tasks complete without keyboard/mouse dependency.

### FR-036
- **Test**: Run long job and observe progress feed.
- **Method**: UI + API integration
- **Scenarios**: Happy + Error (job failure)
- **Pass Criteria**: Timestamped progress entries appear; failure states shown clearly.

### FR-037
- **Test**: Sort and switch contexts repeatedly.
- **Method**: UI performance/integration
- **Scenarios**: Happy
- **Pass Criteria**: No full-page reload; state transitions are immediate and stable.

## 3.8 API and Job Orchestration

### FR-038
- **Test**: Verify endpoint namespace versioning.
- **Method**: Contract tests
- **Scenarios**: Happy
- **Pass Criteria**: Public API exposed under `/api/v1`.

### FR-039
- **Test**: Validate success/error envelope consistency across representative endpoints.
- **Method**: Contract tests
- **Scenarios**: Happy + Error
- **Pass Criteria**: All tested endpoints conform to standard envelope.

### FR-040
- **Test**: Submit long jobs and verify state transitions.
- **Method**: Integration
- **Scenarios**: Happy + Error + Cancel
- **Pass Criteria**: Jobs transition only through valid lifecycle states.

### FR-041
- **Test**: CRUD-style job operations: create/status/list/cancel/progress.
- **Method**: API integration
- **Scenarios**: Happy + Error (unknown job id)
- **Pass Criteria**: Endpoints behave consistently with documented contracts.

### FR-042
- **Test**: CLI service lifecycle and unified process command.
- **Method**: CLI integration
- **Scenarios**: Happy + Error (port in use)
- **Pass Criteria**: Lifecycle commands work and emit actionable diagnostics.

## 3.9 Security, Access, Mode Controls

### FR-043
- **Test**: Localhost mode starts with auth disabled default.
- **Method**: Config/integration
- **Scenarios**: Happy
- **Pass Criteria**: Read/write endpoints accessible locally without auth token.

### FR-044
- **Test**: LAN mode requires auth on mutating endpoints.
- **Method**: Security integration
- **Scenarios**: Happy + Error (missing/invalid token)
- **Pass Criteria**: Unauthorized mutating calls rejected; authorized calls accepted.

### FR-045
- **Test**: CORS behavior in LAN mode.
- **Method**: API security tests
- **Scenarios**: Happy + Error (disallowed origin)
- **Pass Criteria**: Only configured origins allowed; wildcard origin not used.

### FR-046
- **Test**: Submit normalized and malicious file/path inputs.
- **Method**: Security integration
- **Scenarios**: Happy + Error (traversal/injection-like strings)
- **Pass Criteria**: Malicious/invalid paths rejected; valid normalized paths accepted.

## 3.10 Backup, Recovery, Consistency

### FR-047
- **Test**: Backup then restore DB + JSON + galleries index.
- **Method**: Integration + disaster-recovery drill
- **Scenarios**: Happy
- **Pass Criteria**: Restored system matches pre-backup functional state.

### FR-048
- **Test**: Introduce DB/JSON/FS drift and run reconciliation.
- **Method**: Integration
- **Scenarios**: Happy + Edge
- **Pass Criteria**: Drift detected and repaired/reported per policy.

### FR-049
- **Test**: Apply schema migration from prior version.
- **Method**: Migration integration
- **Scenarios**: Happy + Error (interrupted migration)
- **Pass Criteria**: Migration idempotent/recoverable and version updated.

### FR-050
- **Test**: Inspect run summaries for all pipeline modes.
- **Method**: Integration
- **Scenarios**: Happy + Error
- **Pass Criteria**: Summary includes processed/skipped/failed counts + elapsed time.

---

## 4) Non-Functional Acceptance Tests

### NFR-001 (Gallery open p95 < 1.5s)
- **Method**: Performance benchmark on agreed target dataset/profile
- **Pass Criteria**: p95 load < 1.5s

### NFR-002 (Image switch p95 < 100ms perceived)
- **Method**: UI profiling with adjacent preload enabled
- **Pass Criteria**: p95 perceived switch latency < 100ms

### NFR-003 (Command feedback p95 < 50ms)
- **Method**: UI timing instrumentation for non-IO actions
- **Pass Criteria**: p95 feedback latency < 50ms

### NFR-004 (Background jobs non-blocking)
- **Method**: Concurrency UI test during active jobs
- **Pass Criteria**: Navigate + mark picks/rejects without blocking or input lag spikes

### NFR-005 (Adaptive parallelism)
- **Method**: Runtime worker selection test across CPU counts
- **Pass Criteria**: Worker count follows `min(cpu_count-1, configured_cap)` floor 1

### NFR-006 (User parallel cap)
- **Method**: Config + runtime verification
- **Pass Criteria**: User cap applied and observable in job execution

### NFR-007 (Deterministic completion accounting)
- **Method**: Large batch with injected per-item failures
- **Pass Criteria**: Completed/failed/skipped totals reconcile exactly to submitted set

### NFR-008 (Continue-on-error)
- **Method**: Pipeline run with known failing subset
- **Pass Criteria**: Pipeline continues and emits final summarized failures

### NFR-009 (Durable job states)
- **Method**: Restart services mid-job
- **Pass Criteria**: Job state recoverable/reported accurately after restart

### NFR-010 (Health endpoint)
- **Method**: Service health probe tests
- **Pass Criteria**: Readiness reports service + key dependency state

### NFR-011 (Structured logging)
- **Method**: Log schema validation
- **Pass Criteria**: Required fields present in sampled logs

### NFR-012 (Correlation IDs)
- **Method**: Trace single job across logs/events
- **Pass Criteria**: Same correlation ID appears consistently end-to-end

### NFR-013 (Summary metrics)
- **Method**: Metrics endpoint/report validation
- **Pass Criteria**: ingest/proxy/face counts and durations exposed accurately

### NFR-014 (Face data removability)
- **Method**: Privacy operation test
- **Pass Criteria**: Delete flow removes targeted face/person artifacts from DB/API/UI views

### NFR-015 (Destructive op confirmation + audit summary)
- **Method**: Security + audit integration
- **Pass Criteria**: Destructive action requires confirmation and outputs operation summary

### NFR-016 (ExifTool persistent mode efficiency)
- **Method**: Integration benchmark/profile
- **Pass Criteria**: ExifTool process reuse is verified for multi-asset runs; default mode avoids per-file process startup.

### NFR-017 (Persistent mode recovery + deterministic accounting)
- **Method**: Fault-injection integration test
- **Pass Criteria**: Mid-run ExifTool process failure triggers bounded restart/retry; final processed/skipped/failed totals reconcile exactly.

### NFR-018 (External tool preflight diagnostics)
- **Method**: Startup/preflight integration tests
- **Pass Criteria**: Missing/incompatible ExifTool/ImageMagick/RawTherapee dependencies are reported with actionable remediation messages.

---

## 5) Evidence and Sign-off Template

For each requirement, record:

- Requirement ID
- Test run ID / date
- Environment (Linux distro, CPU, RAM, dataset profile)
- Result (Pass/Fail)
- Evidence links (logs, screenshots, benchmark output)
- Notes / defects

Suggested status legend:

- ✅ Pass
- ❌ Fail
- ⚠️ Partial / Needs Clarification
