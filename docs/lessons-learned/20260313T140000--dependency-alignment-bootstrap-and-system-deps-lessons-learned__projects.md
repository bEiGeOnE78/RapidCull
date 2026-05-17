# Dependency Alignment: Bootstrap and System Deps Lessons Learned

Generated: 2026-03-13T14:00:00  
Branch: `feature/dependency-alignment-bootstrap`  
Scope: dependency/process hardening

## 1) Slice Goal

Align dependency documentation, Python dependency source-of-truth, and bootstrap behavior so TDD/dev gates are reproducible and system media dependencies are explicitly verifiable.

---

## 2) What Worked

- Consolidating Python dev/test tooling under `pyproject.toml` `.[dev]` removed bootstrap drift risk.
- Adding Python 3.11 preflight to bootstrap enforces project runtime requirements early.
- Introducing a dedicated system dependency verification script made external media tooling assumptions explicit and testable.

---

## 3) Friction and Fixes

1. **Process miss: branch creation happened after local edits**
   - Some dependency-alignment edits were made on `main` before feature branch creation.
   - Fix: immediately created `feature/dependency-alignment-bootstrap` and continued with approval-first flow.

2. **Dependency source-of-truth mismatch**
   - `scripts/bootstrap.sh` previously installed ad-hoc testing packages instead of using project extras.
   - Fix: bootstrap now installs editable project with `-e ".[dev]"` and runs tool version checks.

---

## 4) Decisions Captured

- `pyproject.toml` is canonical source of Python dev/test dependencies.
- Bootstrap installs from `.[dev]` and Playwright Chromium runtime.
- Linux media/metadata binaries are verified by `scripts/verify_system_deps.sh` before feature work requiring them.

---

## 5) Process Reinforcement

- Keep strict branch-first discipline before any implementation edits.
- Preserve approval gates and stop-on-failure behavior for all subsequent slices.
- Keep dependency docs synchronized with bootstrap and pyproject in the same slice.

---

## 6) Validation Snapshot

- Script syntax checks: pass
- Black: pass
- Ruff: pass
- Mypy: pass
- Pytest full suite: pass (`27 passed`)
