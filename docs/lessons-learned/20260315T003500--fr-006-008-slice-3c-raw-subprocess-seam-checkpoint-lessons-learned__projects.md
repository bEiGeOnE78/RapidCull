# FR-006/007/008 Slice 3c Lessons Learned (RAW Subprocess Seam Checkpoint)

Generated: 2026-03-15T00:35:00  
Branch: `feature/fr-006-007-008-slice-3c-real-subprocess-exec`  
Scope: FR-008a, FR-008b, FR-050a

## 1) Slice Goal

Introduce a concrete subprocess seam in `RawTherapeeAdapter` (`_run_command`) and verify adapter/orchestration behavior remains deterministic with canonical reason mapping.

---

## 2) What Worked

- Moving to an explicit adapter seam (`_run_command`) made subprocess behavior testable without executing external binaries in every test.
- Canonical reason guardrails remained stable while adding subprocess invocation capability.
- Existing deterministic summary assertions continued to protect item/summary reconciliation.

---

## 3) Friction and Fixes

1. **Initial monkeypatch target was invalid**
   - Attempted to patch module-level `subprocess.run` before `subprocess` existed in the adapter module.
   - Fix: patch adapter seam method (`RawTherapeeAdapter._run_command`) instead.

2. **Method monkeypatch signature mismatch**
   - Bound method patch must accept `self` parameter.
   - Fix: update fake method signature to `fake_run_command(self, command)`.

3. **Environment-coupled success assertion for RAW path**
   - Generic orchestration test assumed real tool success, causing instability.
   - Fix: inject deterministic success adapter for generic contract tests; keep subprocess behavior validated in dedicated adapter-focused tests.

---

## 4) Decisions Captured

- `RawTherapeeAdapter` now owns subprocess seam `_run_command(command) -> int`.
- Non-zero subprocess exit maps to canonical `rawtherapee_failed`.
- Generic orchestration contract tests should stay environment-independent via adapter injection.

---

## 5) Process Reinforcement

- Branch created before implementation for slice 3c.
- Approval-first + stop-on-failure followed during RED/GREEN/fix loops.
- Lessons learned captured before commit/PR.

---

## 6) Validation Snapshot

- `black`: pass
- `ruff`: pass
- `mypy`: pass
- full `pytest`: pass (`47 passed`)

---

## 7) Next Slice Suggestions

1. Add equivalent subprocess seam and tests for `ImageMagickAdapter`.
2. Introduce timeout handling + exception taxonomy mapping for RAW subprocess calls.
3. Add real-tool integration test(s) behind explicit dependency assumptions to validate end-to-end subprocess path.
