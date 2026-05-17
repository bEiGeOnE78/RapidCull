# FR-006/007/008 Slice 3d Lessons Learned (ImageMagick Subprocess Seam Checkpoint)

Generated: 2026-03-15T01:15:00  
Branch: `feature/fr-006-007-008-slice-3d-imagemagick-subprocess-seam`  
Scope: FR-006a, FR-007a, FR-008b, FR-050a

## 1) Slice Goal

Introduce ImageMagick subprocess seam parity with RAW adapter patterns, then preserve deterministic orchestration contracts by separating adapter subprocess tests from environment-independent proxy orchestration tests.

---

## 2) What Worked

- Adding `_run_command` seam to `ImageMagickAdapter` enabled direct command-shape testing without requiring real binary success in every orchestration test.
- Canonical still-failure mapping (`imagemagick_still_failed`) remained stable as subprocess execution was introduced.
- Deterministic orchestration tests stayed reliable after introducing explicit success adapter injection for still-success contract paths.

---

## 3) Friction and Fixes

1. **Environment coupling after enabling real still subprocess execution**
   - Existing orchestration tests assumed default still-success behavior and began failing when local command execution returned non-zero.
   - Fix: inject deterministic successful ImageMagick adapter for orchestration-contract tests; keep real subprocess checks in dedicated adapter-level tests.

---

## 4) Decisions Captured

- `ImageMagickAdapter` now has subprocess seam `_run_command(command) -> int` used by still-thumbnail generation.
- Non-zero/exception outcomes map to canonical still failure reason `imagemagick_still_failed`.
- Generic proxy orchestration tests should avoid implicit dependence on local external-binary runtime success.

---

## 5) Process Reinforcement

- Branch created before implementation for slice 3d.
- Approval-first and stop-on-failure workflow followed throughout RED/GREEN loops.
- Lessons-learned artifact recorded before commit/PR.

---

## 6) Validation Snapshot

- `black`: pass
- `ruff`: pass
- `mypy`: pass
- full `pytest`: pass (`48 passed`)

---

## 7) Next Slice Suggestions

1. Add HEIC subprocess seam tests for ImageMagick conversion command paths with canonical reason mapping.
2. Introduce timeout/exception taxonomy handling in ImageMagick adapter similar to RAW evolution path.
3. Add controlled real-tool integration tests for adapter success/failure classes while preserving deterministic orchestrator contracts.
