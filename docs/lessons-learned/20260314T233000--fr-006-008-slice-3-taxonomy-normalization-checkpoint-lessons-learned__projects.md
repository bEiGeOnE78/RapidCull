# FR-006/007/008 Slice 3 Lessons Learned (Taxonomy Normalization Checkpoint)

Generated: 2026-03-14T23:30:00  
Branch: `feature/fr-006-007-008-slice-3-real-subprocess-taxonomy`  
Scope: FR-006a, FR-007a, FR-008a, FR-008b, FR-050a

## 1) Slice Goal

Start slice-3 taxonomy hardening by normalizing adapter-facing failure reasons into stable contract-level reason codes while preserving deterministic proxy accounting and summary reconciliation.

---

## 2) What Worked

- Narrow RED-first increments (one reason-code family at a time) kept changes low-risk and easy to validate.
- Existing deterministic accounting tests from slice 2 made reason migration impacts immediately visible.
- Canonical reason normalization at orchestration boundary avoided leaking ad-hoc adapter/tool message text into public result contracts.

---

## 3) Friction and Fixes

1. **Raw reason-string migration touched multiple assertions**
   - Updating one canonical reason (`rawtherapee_pipeline_unavailable`) required synchronized updates in both item-level and summary-level expectations.
   - Fix: update tests holistically for item + summary contract alignment.

2. **Import-order lint break after adding adapter outcome import**
   - Ruff `I001` failed gate after test expansion.
   - Fix: apply `ruff --fix`, then rerun full quality gates.

---

## 4) Decisions Captured

- Canonical RAW unavailable reason is now `rawtherapee_pipeline_unavailable`.
- Canonical still-thumbnail failure reason is normalized to `imagemagick_still_failed` even if adapter/tool emits non-canonical text.
- Deterministic per-item and per-tool summary contracts remain the authority for externally observed behavior.

---

## 5) Process Reinforcement

- Branch hygiene corrected and enforced at slice start (explicit feature branch before edits).
- Approval-first and stop-on-failure flow maintained through all RED/GREEN and gate-fix steps.
- Lessons-learned artifact captured before commit/PR, per required lifecycle.

---

## 6) Validation Snapshot

- `black`: pass
- `ruff`: pass
- `mypy`: pass
- full `pytest`: pass (`43 passed`)

---

## 7) Next Slice Suggestions

1. Implement real subprocess execution paths in ImageMagick/RawTherapee adapters with secure argument handling and timeout discipline.
2. Add normalized mapping for exit-code/stderr classes into stable reason taxonomy constants.
3. Expand integration coverage for real-tool failure classes without sacrificing deterministic output ordering/reconciliation.
