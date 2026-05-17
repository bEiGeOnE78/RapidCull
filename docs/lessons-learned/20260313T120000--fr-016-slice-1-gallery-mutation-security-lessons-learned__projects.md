# FR-016 Slice 1 Gallery Mutation Security Lessons Learned

Generated: 2026-03-13T12:00:00  
Branch: `feature/fr-016-slice-1-gallery-mutation-security`  
Scope: FR-016 (slice 1)

## 1) Slice Goal

Implement a security baseline for gallery rename/delete operations with explicit allowlist enforcement and traversal/out-of-scope rejection.

---

## 2) What Worked

- Starting with a dedicated FR-016 security integration test file kept scope focused on acceptance behavior (allowed in-scope + rejected invalid paths).
- Implementing path guard helpers in `galleries.py` kept rename/delete logic small and testable.
- Applying full quality gates after targeted TDD validation preserved confidence while minimizing loop time.

---

## 3) Friction and Fixes

1. **Expected RED import failure for missing APIs/models**
   - Initial FR-016 tests failed during collection because `rename_gallery`, `delete_gallery`, and result models did not exist.
   - Fix: add minimal `GalleryRenameResult` / `GalleryDeleteResult` dataclasses and gallery mutation APIs.

2. **Traversal validation needed explicit name constraints**
   - Rename targets can be abused with separator/traversal-like values.
   - Fix: reject invalid `new_name` values (`/`, `\\`, and traversal escapes) and enforce destination allowlist checks before rename.

---

## 4) Decisions Captured

- FR-016 slice 1 scope is mutation baseline only: rename/delete guardrails and rejection semantics.
- Allowlist checks are enforced for both source and destination paths in rename operations.
- Out-of-scope mutations fail fast with explicit permission errors before filesystem changes.

---

## 5) Process Reinforcement

- Keep approval-first flow strict: approval before branch operations, RED tests, implementation, and each lifecycle step.
- Preserve stop-on-failure rule; do not auto-fix command/test failures without user approval.
- Record lessons learned before commit and verify again before PR creation.

---

## 6) Validation Snapshot

- Black: pass
- Ruff: pass
- Mypy: pass
- Pytest full suite: pass (`24 passed`)
