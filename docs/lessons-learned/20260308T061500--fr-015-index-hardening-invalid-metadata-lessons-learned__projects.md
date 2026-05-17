# FR-015 Index Hardening (Invalid Metadata Continuation) Lessons Learned

Generated: 2026-03-08T06:15:00  
Branch: `feature/fr-015-index-hardening`  
Scope: FR-015 (hardening step 1)

## 1) Slice Goal

Harden FR-015 index rebuild so invalid per-gallery metadata does not abort full rebuild and instead records structured failure summaries.

---

## 2) What Worked

- Starting with one hardening test (invalid JSON + continue) kept scope precise and minimized regression risk.
- Extending result models with explicit summary/failure fields made behavior observable and testable.
- Preserving deterministic index output from valid entries kept existing happy-path guarantees intact.

---

## 3) Friction and Fixes

1. **Expected RED due to missing failure model fields**
   - Initial hardening test introduced new summary expectations and failed on missing model/API shape.
   - Fix: add `GalleriesIndexFailure` and expand `GalleriesIndexRebuildResult`.

2. **Backward assertion break in existing happy-path test**
   - Expanded result model caused constructor mismatch in baseline FR-015 test.
   - Fix: update baseline assertion to include zeroed summary/failure fields.

---

## 4) Decisions Captured

- Parse failures in `gallery.json` are recorded as `invalid_metadata_json` and rebuild continues.
- Rebuild summary now reports processed/skipped/failed counts and per-gallery failure details.
- This step intentionally covers malformed JSON path first; missing/unreadable/validation errors remain follow-on hardening slices.

---

## 5) Process Reinforcement

- Continue RED→GREEN→REFACTOR with explicit stop-on-failure and approval before fixes.
- Keep full-suite gate at completion and targeted tests during active TDD loop.
- Capture lessons in both living notes and timestamped artifact before commit.

---

## 6) Validation Snapshot

- Black: pass
- Ruff: pass
- Mypy: pass
- Pytest full suite: pass (`20 passed`)
