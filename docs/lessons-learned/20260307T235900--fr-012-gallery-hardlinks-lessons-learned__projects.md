# FR-012 Gallery Hardlinks Lessons Learned

Generated: 2026-03-07T23:59:00  
Branch: `feature/fr-012-gallery-hardlinks`  
Scope: FR-012

## 1) Slice Goal

Implement the FR-012 baseline by creating virtual galleries via hard links and proving original masters are not modified.

---

## 2) What Worked

- Starting with a single integration RED test kept scope tightly aligned to FR-012 acceptance criteria.
- A dedicated `galleries.py` module maintained domain separation without regressing ingest/proxy behavior.
- Modeling explicit gallery creation results (`GalleryCreationResult`) made outputs deterministic and test-friendly.

---

## 3) Friction and Fixes

1. **Interpreter command mismatch (`python` missing)**
   - Initial test run failed because shell default `python` was unavailable.
   - Fix: standardize on `.venv/bin/python -m ...` for all quality/test commands.

2. **mypy import resolution drift in `src/` layout**
   - mypy treated `rapidcull` as an installed untyped package and raised `py.typed` marker errors.
   - Fix: configure `mypy_path = "$MYPY_CONFIG_FILE_DIR/src"` with existing strict settings and rerun checks.

---

## 4) Decisions Captured

- Implement FR-012 as filesystem-contract-first behavior (hard-link creation + immutability verification) before FR-013 source selection modes.
- Add gallery models in `models.py` and keep gallery orchestration in `galleries.py` to preserve module boundaries.
- Keep this slice free of schema/index persistence changes unless explicitly required by acceptance criteria.

---

## 5) Process Reinforcement

- Continue feature-branch workflow from `main` for each FR slice.
- Keep RED → GREEN → REFACTOR strictness and stop-on-failure with approval-required fixes.
- Capture lessons artifacts in `docs/lessons-learned/` before commit and link in PR notes.

---

## 6) Validation Snapshot

- Black: pass
- Ruff: pass
- Mypy: pass
- Pytest full suite: pass (`13 passed`)
