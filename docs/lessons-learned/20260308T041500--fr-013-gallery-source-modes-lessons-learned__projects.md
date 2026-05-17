# FR-013 Gallery Source Modes Lessons Learned

Generated: 2026-03-08T04:15:00  
Branch: `feature/fr-013-gallery-source-modes`  
Scope: FR-013

## 1) Slice Goal

Implement FR-013 source-selection behavior for gallery creation using query, picks, and face sample modes, including valid empty-gallery behavior for zero matches.

---

## 2) What Worked

- Adding a dedicated FR-013 integration file kept requirement traceability clear while preserving FR-012 baseline regression coverage.
- Reusing FR-012 hard-link creation behavior avoided duplicate filesystem logic.
- Keeping scope to mode selection + empty behavior enabled a fast RED→GREEN loop with low risk.

---

## 3) Friction and Fixes

1. **Expected RED import failure for missing mode API**
   - Test collection failed due to missing `create_gallery_from_mode`.
   - Fix: add minimal mode orchestration function in `galleries.py` and re-run targeted tests.

---

## 4) Decisions Captured

- FR-013 mode selection is implemented as a separate orchestration entry point (`create_gallery_from_mode`) over the FR-012 linking primitive.
- Empty mode results create/retain a valid gallery directory and return an empty success result rather than a failure.
- FR-014/015/016 concerns remain explicitly out of scope for this slice.

---

## 5) Process Reinforcement

- Continue feature-branch-per-slice workflow from current `main`.
- Keep full test suite execution at final gate only; use targeted tests during RED/GREEN.
- Capture lessons artifact + living-notes update before commit and PR.

---

## 6) Validation Snapshot

- Black: pass
- Ruff: pass
- Mypy: pass
- Pytest full suite: pass (`15 passed`)
