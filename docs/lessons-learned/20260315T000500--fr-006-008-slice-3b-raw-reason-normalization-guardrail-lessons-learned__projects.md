# FR-006/007/008 Slice 3b Lessons Learned (RAW Reason Normalization Guardrail)

Generated: 2026-03-15T00:05:00  
Branch: `feature/fr-006-007-008-slice-3b-real-subprocess`  
Scope: FR-008a, FR-008b, FR-050a

## 1) Slice Goal

Add a guardrail ensuring RawTherapee subprocess-detail reason strings do not leak into proxy result contracts, preserving canonical reason taxonomy and deterministic per-tool summary accounting.

---

## 2) What Worked

- A single focused RED test quickly exposed reason-detail leakage risk (`rawtherapee_exit_1` surfacing externally).
- Normalizing reason codes at orchestration boundary preserved adapter flexibility while keeping external contracts stable.
- Existing deterministic summary tests made it straightforward to verify item-level and summary-level reason consistency together.

---

## 3) Friction and Fixes

1. **Adapter detail leaked through orchestration contract**
   - RAW failure path passed through arbitrary adapter reason text.
   - Fix: add explicit normalization function in `proxies.py` that preserves canonical unavailable code and maps all other RAW failures to `rawtherapee_failed`.

---

## 4) Decisions Captured

- Canonical RAW reason contract now behaves as:
  - `rawtherapee_pipeline_unavailable` (preserved when explicit)
  - `rawtherapee_failed` (fallback for any other adapter/tool RAW failure detail)
- Tool-summary reason counts must use the same normalized reason values as failed item records.

---

## 5) Process Reinforcement

- Branch created before implementation for this slice (`feature/fr-006-007-008-slice-3b-real-subprocess`).
- Approval-first and stop-on-failure workflow maintained.
- Lessons-learned artifact recorded before commit/PR.

---

## 6) Validation Snapshot

- `black`: pass
- `ruff`: pass
- `mypy`: pass
- full `pytest`: pass (`44 passed`)

---

## 7) Next Slice Suggestions

1. Implement real subprocess execution in RawTherapee/ImageMagick adapters with bounded timeout and secure args.
2. Normalize ImageMagick subprocess-detail errors through canonical taxonomy helpers (parallel to RAW guardrail pattern).
3. Add real-tool integration tests validating success path and canonical failure mapping under controlled failure conditions.
