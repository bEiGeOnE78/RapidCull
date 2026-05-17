# Foundation Split Lessons Learned (Separation of Concerns)

Generated: 2026-03-07T13:35:00  
Branch: `refactor/split-foundation-by-concern`  
Scope: Behavior-preserving refactor of `foundation.py`

## 1) Goal

Refactor monolithic `foundation.py` into focused modules while preserving public behavior and test parity.

---

## 2) What Worked Well

- Splitting by concern (`schema`, `ingest`, `identity`, `proxies`, `summaries`, `models`) made responsibilities clearer.
- Keeping `foundation.py` as a compatibility re-export layer avoided test and API churn.
- Running parity tests immediately after structural changes caught regressions quickly.

---

## 3) Friction and Fixes

1. **Lint import ordering after refactor**
   - Ruff flagged import ordering in moved modules.
   - Fix: standardize command order (`black` then `ruff --fix` if approved).

2. **Mypy `import-untyped` on internal package imports**
   - Using absolute intra-package imports triggered mypy to treat modules as installed/untyped in this layout.
   - Fix: switch to relative imports (`from .models import ...`, etc.).

---

## 4) Decisions Captured

- Preserve `rapidcull.foundation` import surface during transition via explicit re-exports.
- Keep functional boundaries small and explicit to reduce future merge conflicts and simplify testing.
- Treat structural refactors as first-class slices with full quality gates, not as incidental cleanups.

---

## 5) Process Reinforcement

- Lessons learned captured before commit and before PR creation (process gate satisfied).
- Continue requiring behavior parity test runs for all structural refactors.

---

## 6) Validation Snapshot

- Black: pass
- Ruff: pass
- Mypy: pass
- Pytest integration slice: pass (`9 passed`)
