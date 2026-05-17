# Query Stale Doc Cleanup v1 Lessons Learned

Generated: 2026-03-31T15:09:19-05:00  
Branch: `feature/query-stale-doc-cleanup-v1`  
Scope: Query documentation cleanup

## 1) Slice Goal

Correct the stale canonical example in the Query Evaluation Contract v1 document so the published documentation matches the already-approved and implemented any-value behavior for multi-value text equality.

---

## 2) What Worked

- Keeping the slice to one concrete contradiction made the cleanup fast and low-risk.
- Adding a minimal doc verification assertion before the edit ensured the stale example was captured by executable coverage rather than fixed only by inspection.
- Reusing the existing query contract doc-smoke test kept the verification path simple and aligned with the established documentation process.

---

## 3) Friction and Fixes

1. **The stale example had already propagated across merged spec and implementation work**
   - The evaluation contract still said `person=bob -> non-match` even after semantics clarification and evaluator implementation had settled on any-value matching.
   - Fix: add a targeted verification assertion first, confirm the RED failure, then correct the contract example.

2. **It was easy to treat a doc-only correction as exempt from full gates**
   - The first pass only reran the focused doc verification test.
   - Fix: stop, acknowledge the miss, and run the full required validation sequence before calling the slice complete.

---

## 4) Decisions Captured

- Canonical documentation examples must match approved runtime behavior exactly once implementation lands.
- A narrow stale-doc slice can reuse the existing doc-smoke test file instead of inventing a separate verification path.
- Even doc-only slices should still complete the full validation gates when they change machine-checked contract documentation.

---

## 5) Process Reinforcement

- RED → GREEN remains useful for documentation corrections when the docs act as executable contract artifacts.
- Full validation gates should be run before post-slice documentation updates, even when the change appears trivial.
- Lessons learned and living-notes updates remain part of done-ness for doc cleanup slices, not just implementation slices.

---

## 6) Validation Snapshot

- Focused Pytest: pass (`.venv/bin/python -m pytest tests/integration/query` → `42 passed`)
- Full Pytest: pass (`.venv/bin/python -m pytest` → `96 passed`)
- Black: pass (`.venv/bin/python -m black --check .`)
- Ruff: pass (`.venv/bin/python -m ruff check .`)
- Mypy: pass (`.venv/bin/python -m mypy src`)

---

## 7) Next Slice Suggestions

1. Add parser-to-evaluator end-to-end coverage that starts from query text, parses it, and evaluates it against normalized records.
2. After record-level evaluation coverage is stable, consider a collection-filtering slice built on the existing evaluator baseline.
