# FR-014 Rebuild-All Galleries Metadata Lessons Learned

Generated: 2026-03-08T05:05:00  
Branch: `feature/fr-014-rebuild-all-galleries-metadata`  
Scope: FR-014 (sub-slice: rebuild all galleries)

## 1) Slice Goal

Implement the second FR-014 slice: rebuild `gallery.json` metadata across all gallery directories by orchestrating over the existing single-gallery rebuild primitive.

---

## 2) What Worked

- Extending the existing FR-014 integration file preserved requirement traceability while keeping prior single-gallery tests intact.
- Composition over duplication (`rebuild_all_galleries_metadata` -> `rebuild_gallery_metadata`) kept logic concise and consistent.
- Deterministic directory iteration produced stable summary ordering and predictable assertions.

---

## 3) Friction and Fixes

1. **Expected RED import failures for new rebuild-all API/model**
   - Test collection initially failed due to missing `rebuild_all_galleries_metadata` and `GalleryMetadataRebuildSummary`.
   - Fix: add minimal model + orchestration function and rerun targeted FR-014 tests.

2. **Strict Pylance payload typing warning**
   - `payload` dictionary in metadata rebuild path showed partially unknown type warning.
   - Fix: define explicit `TypedDict` (`GalleryMetadataPayload`) and annotate payload for clearer static typing.

---

## 4) Decisions Captured

- Keep FR-014 rebuild-all behavior as orchestration only; single-gallery primitive remains source of truth for metadata semantics.
- Return typed summary (`GalleryMetadataRebuildSummary`) for deterministic, testable fanout results.
- Preserve existing explicit missing-path behavior at single-gallery boundary.

---

## 5) Process Reinforcement

- Continue RED→GREEN→REFACTOR with targeted tests and full-suite gate at completion.
- Keep lessons capture mandatory before commit/PR, including sub-slice artifacts.
- Use approval-first git workflow gates for commit/push, PR creation, and merge/delete.

---

## 6) Validation Snapshot

- Black: pass
- Ruff: pass
- Mypy: pass
- Pytest full suite: pass (`18 passed`)
