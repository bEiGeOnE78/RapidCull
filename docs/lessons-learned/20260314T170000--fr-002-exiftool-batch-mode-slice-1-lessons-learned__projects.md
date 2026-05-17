# FR-002 ExifTool Batch Mode Slice 1 Lessons Learned

Generated: 2026-03-14T17:00:00  
Branch: `feature/fr-002-exiftool-batch-mode-slice-1`  
Scope: FR-002a..d / NFR-016/017 foundation

## 1) Slice Goal

Introduce an ExifTool-backed metadata extraction foundation for ingest with persistent batch-mode transport semantics, deterministic per-asset mapping, and continue-on-error accounting.

---

## 2) What Worked

- Splitting extraction into two adapters (test seam + real tool adapter) made incremental TDD possible without blocking on environment setup for every loop.
- Using ExifTool `-stay_open` with numbered `-executeN` markers produced a clear request/response boundary model.
- Canonical normalization at ingest boundary (`file_type`, `capture_datetime`, `camera_make`, `camera_model`) reduced downstream coupling to ExifTool group naming.

---

## 3) Friction and Fixes

1. **Tool availability assumptions caused gate failures**
   - Real integration tests initially skipped on missing `exiftool`; policy was updated to fail fast for critical system tools.
   - Fix: enforce hard failure in tests when required tool is missing.

2. **Fixture fragility with embedded base64 image**
   - Initial fixture payload was malformed and failed decode.
   - Fix: generate minimal JPEG fixture via ImageMagick (`magick`/`convert`) inside test setup, then stamp metadata via ExifTool.

3. **ExifTool group/key variability (`Unknown:*`, etc.)**
   - Assertions against fixed group names (`EXIF:`, `IFD0:`) failed on real output.
   - Fix: normalize raw metadata to canonical fields with multi-key fallback strategy including `Unknown:*` variants.

---

## 4) Decisions Captured

- Critical tool-dependent tests should fail (not skip) when dependencies are missing.
- Canonical field contracts are preferred over direct group-specific ExifTool key assertions.
- Continue-on-error behavior for per-item extraction failures remains mandatory.

---

## 5) Follow-up Hardening (Recommended)

- Request explicit tags from ExifTool per call (instead of broad output) to reduce key-shape variability.
- Add fixture matrix beyond synthetic JPEG (HEIC/RAW and representative camera outputs).
- Add restart/timeout retry behavior and tests for persistent process interruption scenarios.

---

## 6) Validation Snapshot

- Black: pass
- Ruff: pass
- Mypy: pass
- Pytest full suite: pass (`32 passed`)
