# Photo Library Test Plan (Linux-Only)

Generated: 2026-03-07T08:27:00  
Scope Source: `20260307T080227--photo-library-requirements__projects.md`  
Acceptance Source: `20260307T080227--photo-library-acceptance-tests__projects.md`

## 1) Objective

Execute a fast, parallel, repeatable validation process to prove FR-001..FR-050 and NFR-001..NFR-015 are met for the Linux-only baseline.

## 2) Test Framework and Tooling

## 2.1 Primary Framework

- **Pytest** (primary test runner)
- **pytest-xdist** (parallel execution)
- **pytest-cov** (coverage reporting)
- **pytest-benchmark** (NFR latency/perf checks)

## 2.2 UI Framework

- **Playwright (Python bindings)** for browser-based UI tests
  - keyboard workflows
  - command palette
  - touch/culling flows
  - gallery/single-view interactions

## 2.3 Supporting Utilities

- `coverage.py` (if needed directly)
- JSON schema assertions inside pytest for API envelope checks
- Optional shell helpers for environment orchestration
- ExifTool persistent mode harness/fixture for batch metadata extraction validation
- External tool capability checks for ImageMagick HEIF support and RawTherapee CLI profile availability

## 2.4 Why this stack

- Single-language test ecosystem (Python) for speed and maintainability
- Strong parallel support (`xdist`) aligned with project priority on fast execution
- Suitable for API, integration, and UI in one coordinated workflow

---

## 3) Environment and Baseline

## 3.1 Platform

- **Linux only** (required)

## 3.2 Test Environments

- **Dev-local:** fast iteration, subset datasets
- **Pre-release validation:** full representative dataset profile

## 3.3 Dataset Profiles

- **Small:** smoke + parser + security checks
- **Medium:** core integration + job lifecycle
- **Target profile:** NFR performance validation (must be documented per run)

## 3.4 Required Runtime Services

- Static/gallery server (port 8000)
- Face/core API (port 8001)
- Gallery API (port 8002)

---

## 4) Test Scope Mapping

- **Functional:** FR-001..FR-050
- **Non-functional:** NFR-001..NFR-015
- **Modes:** localhost + LAN mode (auth/cors differences)
- **Out of scope:** non-Linux platform certification

---

## 5) Execution Strategy (Parallel-First)

## 5.1 Phase 0 — Preflight (sequential)

1. Verify Linux environment + dependencies
2. Verify test dataset availability
3. Start required services
4. Validate health/readiness endpoints

Preflight dependency checks shall explicitly verify ExifTool, ImageMagick (`magick`/`convert`), and RawTherapee CLI availability/capability before running related ingest/proxy phases.

Exit criteria:
- Services healthy
- Dataset mounted/accessible
- Test runner operational

## 5.2 Phase 1 — Core Parallel Batch A

Run in parallel:
- Ingestion/indexing (FR-001..005)
- Query grammar (FR-017..022)
- Security mode controls (FR-043..046)

Goal:
- Validate foundational behavior quickly
- Validate ExifTool persistent batch-mode metadata extraction behavior, deterministic per-asset mapping, and partial-failure accounting paths

## 5.3 Phase 2 — Core Parallel Batch B (depends on A)

Run in parallel:
- Proxy generation (FR-006..011)
- Face operations (FR-023..028)
- Gallery lifecycle (FR-012..016)

Goal:
- Validate heavy-processing domains with adaptive worker caps
- Validate FR-015 index rebuild hardening (partial metadata failures, empty-state behavior, deterministic output)
- Validate ImageMagick deterministic proxy behavior and RawTherapee profile-driven RAW conversion with non-blocking error reporting

## 5.4 Phase 3 — Core Parallel Batch C (depends on A+B)

Run in parallel:
- UI interactions (FR-033..037, Playwright)
- API/job orchestration (FR-038..042)
- Backup/recovery/consistency (FR-047..050)

Goal:
- Validate end-user behavior + orchestration reliability

## 5.5 Phase 4 — NFR Validation (cross-cutting)

- NFR-001..015
- Benchmark/perf suite on target dataset profile
- Reliability and observability checks

Goal:
- Confirm speed, parallelism, resilience, and safety requirements

---

## 6) Suggested Test Suite Layout

```text
tests/
  unit/
  integration/
    ingest/
    proxies/
    galleries/
    face/
    api/
    security/
    backup_recovery/
  ui/
    playwright/
  nfr/
    performance/
    reliability/
    observability/
```

Tag/marker guidance:

- `@pytest.mark.fr`
- `@pytest.mark.nfr`
- `@pytest.mark.ui`
- `@pytest.mark.integration`
- `@pytest.mark.slow`
- `@pytest.mark.security`
- `@pytest.mark.performance`

---

## 7) Command Strategy (Example)

## 7.1 Fast local feedback

```bash
pytest -q -m "not slow" -n auto
```

## 7.2 Batch execution (parallel)

```bash
# Batch A
pytest -q tests/integration/ingest tests/integration/security tests/integration/api/test_query_* -n auto

# Batch B
pytest -q tests/integration/proxies tests/integration/face tests/integration/galleries -n auto

# Batch C
pytest -q tests/ui/playwright tests/integration/api tests/integration/backup_recovery -n auto
```

## 7.3 NFR runs

```bash
pytest -q tests/nfr/performance --benchmark-only
pytest -q tests/nfr/reliability tests/nfr/observability
```

## 7.4 Coverage reporting

```bash
pytest -q --cov=. --cov-report=term-missing --cov-report=xml
```

---

## 8) Quality Gates and Exit Criteria

## 8.1 Functional Gate

- All critical FR tests pass
- No open critical defects

## 8.2 NFR Gate

- NFR-001/002/003 latency targets met at p95 on target dataset profile
- NFR-005/006/007 parallelism and accounting checks pass
- NFR-008..018 reliability/observability/privacy/tooling checks pass

Toolchain gate:
- ExifTool/ImageMagick/RawTherapee preflight must pass (or tests must validate expected actionable failure handling paths).
- External-tool failure accounting must reconcile to final processed/skipped/failed summaries.

## 8.3 Coverage Gate (from testing standards)

- Critical areas: 100%
- High-priority areas: 90%+
- Medium-priority areas: 80%+

## 8.4 Release Readiness Gate

- API envelope consistency validated (FR-039)
- Job lifecycle semantics validated (FR-040/041)
- Backup/restore/reconcile validated (FR-047/048)

---

## 9) Defect Management Workflow

1. Capture failing requirement ID(s)
2. Attach evidence (logs, screenshot/video, benchmark output)
3. Classify severity: Critical / High / Medium / Low
4. Reproduce and isolate (unit vs integration vs env)
5. Re-run targeted suite, then affected batch, then full gate if critical

Stop rule:

- If any critical gate fails, do not proceed to release sign-off.

---

## 10) Reporting and Evidence

Per run, record:

- Run ID + timestamp
- Commit/revision under test
- Environment (Linux distro/kernel, CPU/RAM)
- Dataset profile (small/medium/target)
- Batch results (A/B/C/D)
- FR/NFR pass-fail summary
- Coverage summary
- Benchmark summary (p50/p95/p99 where applicable)
- Defect list + disposition

---

## 11) Risks and Mitigations

- **Risk:** Performance variance by hardware
  - **Mitigation:** Track hardware profile and normalize comparisons by target profile

- **Risk:** Flaky UI timings under load
  - **Mitigation:** deterministic fixtures, retries only for known transient infra causes, separate perf and functional runs

- **Risk:** Data drift between DB/JSON/FS
  - **Mitigation:** mandatory reconciliation check in Batch C and pre-release gate

---

## 12) Framework Decision (Answer)

The test framework used is:

- **Pytest** as the unified test runner
- **pytest-xdist** for parallel execution
- **Playwright (Python)** for UI end-to-end validation
- **pytest-benchmark** for performance/NFR validation
- **pytest-cov** for coverage enforcement
