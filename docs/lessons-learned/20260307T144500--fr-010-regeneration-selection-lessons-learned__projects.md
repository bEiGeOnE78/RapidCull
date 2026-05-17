# FR-010 Regeneration Selection Lessons Learned

Generated: 2026-03-07T14:45:00  
Branch: `feat/fr-010-regeneration-selection`  
Scope: FR-010

## 1) Slice Goal

Add regeneration selection behavior supporting both selected-ID and bulk modes, including invalid-ID reporting without halting execution.

---

## 2) What Worked

- Extending the proxy module with a dedicated selection function kept concerns clean.
- Dataclass-based result modeling made selected/bulk mode behavior explicit and testable.
- Invalid-ID handling stayed deterministic and easy to assert in tests.

---

## 3) Friction and Fixes

1. **Import ordering drift in expanded test module**
   - Ruff detected import sort mismatch after adding FR-010 symbols.
   - Fix: run `ruff --fix` after formatting when approved.

---

## 4) Decisions Captured

- `selected_ids=None` maps to `bulk` mode (all available assets).
- Unknown IDs are accumulated in `invalid_ids` while valid IDs continue processing.
- Result includes explicit mode indicator (`selected` / `bulk`) for downstream reporting.

---

## 5) Process Reinforcement

- Lessons learned captured before commit and PR creation.
- Keep adding logic to focused modules (`proxies.py`, `models.py`) and not to façade layers.

---

## 6) Validation Snapshot

- Black: pass
- Ruff: pass
- Mypy: pass
- Pytest integration slice: pass (`11 passed`)
