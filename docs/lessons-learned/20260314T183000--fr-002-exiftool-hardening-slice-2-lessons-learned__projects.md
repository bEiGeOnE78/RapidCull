# FR-002 ExifTool Hardening Slice 2 Lessons Learned

Generated: 2026-03-14T18:30:00  
Branch: `feature/fr-002-exiftool-hardening-slice-2`  
Scope: FR-002 hardening (explicit tags + transport recovery)

## 1) Slice Goal

Harden ExifTool persistent metadata extraction by narrowing output to explicit requested tags, adding bounded transport recovery (restart + single retry), and preserving deterministic failure accounting.

---

## 2) What Worked

- Explicit tag requests per ExifTool execution reduced output payload noise and focused extraction on canonical ingest fields.
- Restart + single-retry policy handled transient transport failures while preserving deterministic processed/failed accounting.
- Keeping recovery behavior testable through seam adapter methods (`enqueue_transport_failure`) enabled stable RED→GREEN iteration.

---

## 3) Friction and Fixes

1. **Transport timeout implementation with `select` + text streams proved fragile**
   - Real integration tests regressed with `tool_error` despite healthy toolchain.
   - Root issue: mixing fd-readiness polling with buffered text wrappers can produce brittle behavior.
   - Fix: switched to bounded elapsed-time loop around blocking `readline()` and marker detection.

2. **Error taxonomy normalization required deterministic output contract**
   - Retry-exhausted transport failures needed stable ingest summary semantics.
   - Fix: map exhausted `transport_error` to deterministic `tool_error` in ingest failure accounting.

---

## 4) Decisions Captured

- ExifTool request contract now explicitly requests required tags only.
- Persistent-process recovery policy is bounded: restart once and retry once per item.
- Full-gate behavior remains fail-fast for missing required tool dependencies.

---

## 5) Follow-up Hardening (Recommended)

- Move subprocess communication to bytes-mode protocol parsing for stronger control over buffering and timeout behavior.
- Add targeted interruption tests for forced process termination mid-batch in real integration path.
- Expand canonical metadata coverage incrementally (ISO/fnumber/focal/lens/date precedence variants).

---

## 6) Validation Snapshot

- Black: pass
- Ruff: pass
- Mypy: pass
- Pytest full suite: pass (`34 passed`)
