# Photo Library Execution Checklist (Linux-Only)

Generated: 2026-03-07T09:15:00  
Companion To:  
- `20260307T080227--photo-library-requirements__projects.md`  
- `20260307T080227--photo-library-acceptance-tests__projects.md`  
- `20260307T080227--photo-library-test-plan__projects.md`  
- `20260307T090000--photo-fixture-dataset-test-plan__projects.md`

## 1) Purpose

This document is an operator-facing checklist for running development and validation cycles with TDD (red-green-refactor). It complements existing plan/spec docs by providing run-by-run control steps, go/no-go gates, and evidence tracking.

---

## 2) Run Metadata (Fill Before Start)

- [ ] Run ID:
- [ ] Date/Time (UTC):
- [ ] Branch:
- [ ] Commit SHA:
- [ ] Operator:
- [ ] Linux distro/kernel:
- [ ] CPU/RAM profile:
- [ ] Dataset profile: Small / Medium / Target
- [ ] Mode: Localhost / LAN

---

## 3) Preflight Checklist (Go/No-Go)

## 3.1 Environment

- [ ] Python version matches project requirement (`>=3.11`)
- [ ] Virtual environment activated
- [ ] Dependencies installed
- [ ] Playwright browser runtime installed (Chromium)

## 3.2 Services and Ports

- [ ] Static/gallery service available (port 8000)
- [ ] Face/core API available (port 8001)
- [ ] Gallery API available (port 8002)
- [ ] Health/readiness endpoints responding

## 3.3 Dataset Readiness

- [ ] Fixture manifest selected (`small.yaml` / `medium.yaml` / `target.yaml`)
- [ ] Required media mix present (image/RAW/HEIC/video/invalid)
- [ ] License/provenance recorded for non-repo datasets
- [ ] Face dataset usage approved (if applicable)

**Go/No-Go Rule**: Do not begin Batch A until all preflight items are checked.

---

## 4) TDD Cycle Checklist (Per Requirement Slice)

For each selected FR/NFR slice:

- [ ] Requirement IDs selected (example: FR-001..003)
- [ ] RED tests written from requirement behavior
- [ ] RED run confirms failure for expected reason
- [ ] GREEN implementation added minimally
- [ ] GREEN run confirms passing tests
- [ ] REFACTOR completed with tests still passing
- [ ] Formatter/linter run and clean
- [ ] Evidence linked (test output, notes)

Suggested owner/timestamp fields per slice:

- Owner:
- Start:
- End:
- Result: Pass / Fail / Partial

---

## 5) Batch Execution Checklist

## 5.1 Batch A (Foundational)

Scope:
- FR-001..005
- FR-017..022
- FR-043..046

Checklist:

- [ ] Batch A tests executed in parallel where applicable
- [ ] All critical failures triaged
- [ ] Foundational schema/query/security behaviors validated

Gate:

- [ ] **GO to Batch B** only if critical A failures = 0

## 5.2 Batch B (Processing Domains)

Scope:
- FR-006..011
- FR-012..016
- FR-023..028

Checklist:

- [ ] Proxy generation checks completed
- [ ] Gallery lifecycle checks completed
- [ ] Face operations checks completed
- [ ] Error-path handling verified (continue-on-error behavior)

Gate:

- [ ] **GO to Batch C** only if critical B failures = 0

## 5.3 Batch C (UI/API/Recovery)

Scope:
- FR-033..037
- FR-038..042
- FR-047..050

Checklist:

- [ ] UI interaction suite completed
- [ ] API envelope and versioning checks passed
- [ ] Job lifecycle and control endpoints validated
- [ ] Backup/restore/reconciliation checks passed

Gate:

- [ ] **GO to Batch D** only if critical C failures = 0

## 5.4 Batch D (NFR)

Scope:
- NFR-001..015

Checklist:

- [ ] Performance benchmarks collected (p50/p95/p99 where applicable)
- [ ] Parallelism and accounting behavior validated
- [ ] Reliability and restart behavior validated
- [ ] Structured logging and correlation IDs validated
- [ ] Privacy/safety deletion workflows validated

Gate:

- [ ] **Release candidate eligible** only if NFR gate criteria met

---

## 6) Failure Branch Actions (Report-First)

If any critical test fails:

- [ ] Stop progression to next batch
- [ ] Capture failing requirement IDs
- [ ] Capture evidence (logs, screenshots/video, benchmark output)
- [ ] Classify severity (Critical/High/Medium/Low)
- [ ] Open/record defect with reproduction notes
- [ ] Execute targeted rerun after fix
- [ ] Re-run affected batch before proceeding

Escalation contact(s):

- Engineering lead:
- QA lead:
- Product owner:

---

## 7) Artifact Checklist (Expected Outputs)

- [ ] Test result output archived
- [ ] Coverage report generated (terminal + XML)
- [ ] Benchmark output archived for NFR runs
- [ ] UI evidence captured for UI failures (screenshots/videos)
- [ ] Run summary generated (processed/skipped/failed + elapsed)
- [ ] Defect list updated

Artifact locations:

- Coverage XML path:
- Benchmark logs path:
- Test report path:
- Screenshot/video path:
- Run summary path:

---

## 8) Rerun Policy Checklist

- [ ] Unit-level fix only → rerun targeted unit/integration subset
- [ ] Shared core behavior changed → rerun full affected batch
- [ ] Critical defect fixed → rerun affected batch + regression subset
- [ ] Release gate impact → rerun full gate path (A→D as needed)

---

## 9) Branch and PR Checklist (Per TDD Slice)

- [ ] Feature branch created
- [ ] Commits reflect RED → GREEN → REFACTOR progression
- [ ] PR includes requirement IDs and test evidence links
- [ ] CI checks pass (format/lint/tests)
- [ ] Reviewer sign-off obtained

Branch:
- Name:

PR:
- URL:

---

## 10) Final Sign-Off Block

Functional gate:
- [ ] Pass

NFR gate:
- [ ] Pass

Security/privacy checks:
- [ ] Pass

Release recommendation:
- [ ] Go
- [ ] No-Go

Approvals:

- QA: __________________  Date: __________
- Engineering: __________  Date: __________
- Product: ______________  Date: __________
