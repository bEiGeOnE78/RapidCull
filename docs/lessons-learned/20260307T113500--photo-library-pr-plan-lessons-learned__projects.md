# Photo Library PR Plan Lessons Learned (FR-001..003 Slice)

Generated: 2026-03-07T11:35:00  
Branch: `feat/fr-001-003-foundation`  
Scope: FR-001, FR-002, FR-003

## 1) Objective of This Slice

Validate the first foundational TDD slice using red-green-refactor with requirement-defined behavior:

- FR-001: SQLite schema initialization and version validation
- FR-002: Supported media discovery
- FR-003: Incremental processing via fingerprint and force mode

---

## 2) What Worked Well

1. **Requirements-driven tests gave clear implementation boundaries**
   - Writing RED tests first kept scope tight and prevented overbuilding.

2. **Small slice size improved reviewability**
   - Limiting to FR-001..003 made failures understandable and fixes incremental.

3. **Tooling standardization improved code quality quickly**
   - Black + Ruff setup caught formatting/import hygiene issues early.

4. **Stop-on-failure handling reduced risk**
   - Each error was surfaced, proposed, and approved before change.

---

## 3) Friction Points Encountered

1. **Initial test runner mismatch**
   - `pytest` was not available on PATH.
   - Resolution: use interpreter-bound command (`python -m pytest`) and bootstrap venv.

2. **Python version drift (3.10 vs required >=3.11)**
   - Editable install failed because project metadata required 3.11+.
   - Resolution: install and use pyenv-managed Python 3.11.11.

3. **pyenv build missing stdlib modules**
   - `_bz2`, `readline`, `_ssl` absent on first build.
   - Resolution: install OS build dependencies, rebuild Python.

4. **Environment reset after venv recreation**
   - Recreated venv no longer had pytest stack installed.
   - Resolution: reinstall test dependencies before re-running checks.

---

## 4) Decisions Made

1. **Use TDD as default delivery mode** (RED → GREEN → REFACTOR).
2. **Keep project runtime target at Python >=3.11** (no metadata downgrade).
3. **Use pyenv for local interpreter management** to avoid system-default disruption.
4. **Adopt Black + Ruff for formatting/linting baseline** in this early phase.

---

## 5) Process Improvements for Next Slices

Before starting the next feature branch, run this preflight checklist:

- [ ] `.venv/bin/python --version` confirms 3.11+
- [ ] `.venv/bin/python -m pytest --version` works
- [ ] `.venv/bin/python -m black --version` works
- [ ] `.venv/bin/python -m ruff --version` works
- [ ] `.venv/bin/python -m playwright --version` works

And for each slice:

- [ ] Write failing tests mapped to explicit FR IDs
- [ ] Implement minimum behavior only
- [ ] Run black + ruff + targeted pytest
- [ ] Capture failures as lessons and update checklist docs

---

## 6) Validation Outcome for This Slice

- FR-001..003 targeted tests: **Pass**
- Formatting (Black): **Pass**
- Linting (Ruff): **Pass**
- Status: **Ready for commit/review as first foundation slice**

---

## 7) Recommended Next Slice

Proceed with FR-004..005 using the same TDD cycle:

- FR-004: Stable `image_id` across DB/JSON/API contracts
- FR-005: Failed ingest recording with reason + run summary surfacing
