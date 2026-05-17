# FR-015 Galleries Index Refresh Lessons Learned

Generated: 2026-03-08T05:45:00  
Branch: `feature/fr-015-galleries-index-refresh`  
Scope: FR-015 (slice 1)

## 1) Slice Goal

Implement a deterministic central galleries index rebuild primitive that derives `galleries_index.json` from current per-gallery metadata for UI/API consumption.

---

## 2) What Worked

- A dedicated FR-015 integration file kept requirement mapping explicit and review-friendly.
- Building index entries from existing `gallery.json` files reused established FR-014 metadata contracts.
- Deterministic sorting (`gallery_path`) produced stable index output and predictable assertions.

---

## 3) Friction and Fixes

1. **Expected RED import failure for missing index API/model**
   - Initial FR-015 test failed at collection due to missing `rebuild_galleries_index` and result model.
   - Fix: add minimal typed models and index rebuild primitive.

2. **Readability concern in gallery-dir iteration**
   - Inline sorted generator in loop reduced readability.
   - Fix: split into named `gallery_dirs` list before iteration.

---

## 4) Decisions Captured

- Keep FR-015 slice 1 focused on deterministic happy-path index rebuild only.
- Store central index at `galleries_root / "galleries_index.json"`.
- Skip directories lacking `gallery.json` instead of failing this baseline slice.

---

## 5) Process Reinforcement

- Continue RED→GREEN→REFACTOR with targeted tests, then full gate run.
- Preserve explicit approval gates for all git lifecycle steps.
- Capture lessons in both detailed artifact and living notes before commit.

---

## 6) Validation Snapshot

- Black: pass
- Ruff: pass
- Mypy: pass
- Pytest full suite: pass (`19 passed`)
