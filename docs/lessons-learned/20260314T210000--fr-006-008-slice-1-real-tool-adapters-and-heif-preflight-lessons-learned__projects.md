# FR-006/007/008 Slice 1 Lessons Learned (Real-Tool Adapters + HEIF Preflight)

Generated: 2026-03-14T21:00:00  
Branch: `feature/fr-006-007-008-slice-1`  
Scope: FR-006a, FR-007a, FR-008a, FR-008b, NFR-007, NFR-008, NFR-018, FR-050a

## 1) Slice Goal

Move proxy generation from baseline modeling toward real-tool adapter seams while preserving deterministic per-item accounting, and enforce HEIC/HEIF capability as an explicit preflight requirement.

---

## 2) What Worked

- Incremental TDD (RED → GREEN) surfaced contract gaps early and avoided broad refactors.
- Adapter seams (`ImageMagickAdapter`, `RawTherapeeAdapter`) kept proxy orchestration testable with explicit dependency injection.
- Deterministic tests were preserved across environments by injecting capability states (`heif_supported=True/False`) instead of relying only on host state.
- System preflight upgrade (`verify_system_deps.sh`) added practical fail-fast diagnostics for missing HEIF support and aligned with dependency policy.

---

## 3) Friction and Fixes

1. **Runtime capability detection changed default HEIC behavior**
   - Once default HEIF detection was added, a failure-path test became host-dependent and failed on machines with HEIF support.
   - Fix: make failure-path test deterministic via explicit adapter injection (`ImageMagickAdapter(heif_supported=False)`).

2. **Environment command invocation mismatch (`python` not found)**
   - Initial test command failed due to pyenv shell command resolution.
   - Fix: use interpreter-bound command convention (`.venv/bin/python -m ...`) consistently.

---

## 4) Decisions Captured

- Treat HEIC/HEIF support as a **required runtime capability** (not only package presence) and check it in preflight.
- Keep proxy execution deterministic and continue-on-error via per-item `generated`/`failed` outcomes with stable reason strings.
- Use runtime capability detection for default adapter behavior, but require explicit injected adapter behavior in tests for deterministic failure/success coverage.

---

## 5) Process Reinforcement

- Approval gate respected for each implementation/test step.
- Stop-on-failure rule followed: reported failures first, then applied fixes only after approval.
- Lessons-learned artifact added before commit/PR per process requirement.

---

## 6) Validation Snapshot

- `scripts/verify_system_deps.sh`: pass (with HEIF capability check enabled)
- `black`: pass
- `ruff`: pass
- `mypy`: pass
- `pytest` full suite: pass (`39 passed`)

---

## 7) Follow-up Suggestions

1. Add adapter-level integration tests that execute real ImageMagick/RawTherapee commands on fixture assets and map tool stderr/exit codes to stable reason taxonomy.
2. Introduce explicit proxy-run summary model with per-tool counts to satisfy FR-050a reporting depth beyond current item-level result lists.
