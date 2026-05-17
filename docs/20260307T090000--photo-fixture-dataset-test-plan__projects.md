# Photo Fixture and Dataset Test Plan (Linux-Only)

Generated: 2026-03-07T09:00:00  
Scope Sources:  
- `20260307T080227--photo-library-requirements__projects.md`  
- `20260307T080227--photo-library-acceptance-tests__projects.md`  
- `20260307T080227--photo-library-test-plan__projects.md`

## 1) Objective

Define a repeatable, legally safe, TDD-friendly data strategy for validating FR-001..FR-050 and NFR-001..NFR-015.

This plan supports red-green-refactor cycles by separating deterministic small fixtures from heavier integration and performance datasets.

---

## 2) Three-Tier Dataset Strategy

## 2.1 Tier 0 — Deterministic Unit Fixtures (In-Repo)

**Purpose**: Fast, stable RED tests and local refactor safety.  
**Size target**: ~30–80 files.

Recommended composition:

- 10 still images (JPG/PNG) with mixed EXIF presence
- 2 HEIC files
- 2 RAW files (e.g., `.CR2`, `.NEF`)
- 2 small video files (`.mp4`)
- 4 intentionally invalid/corrupt files
- Filename/path edge cases:
  - spaces
  - unicode
  - long names
  - nested folders
  - symlink case

**Use for**:

- FR-001..005 core behavior tests
- Query parser/operator validation stubs (FR-017..022)
- Security/path normalization tests (FR-043..046)

## 2.2 Tier 1 — Integration Dataset (Downloaded + Cached)

**Purpose**: Domain acceptance and end-to-end integration confidence.  
**Size target**: ~1,000–5,000 assets.

Recommended composition:

- Majority JPG/PNG
- Enough HEIC/RAW/video to validate proxy paths
- Multi-folder structure with realistic metadata diversity

**Use for**:

- Batch A/B/C acceptance execution
- Job lifecycle, API envelope, and UI integration checks

## 2.3 Tier 2 — Performance Benchmark Dataset (Not in Repo)

**Purpose**: NFR gate verification on target profile.  
**Size target**: 20,000+ assets (or agreed target profile).

**Use for**:

- Batch D NFR validation only
- p95 latency and throughput measurements
- resilience and observability checks under realistic load

---

## 3) Candidate Data Sources by Coverage Need

## 3.1 General Ingestion/Metadata

- COCO
- Open Images
- Wikimedia Commons / similarly permissive sources

## 3.2 Face Detection/Clustering Coverage

- LFW
- CelebA
- WIDER FACE

Note: Face datasets require explicit license/privacy review before use.

## 3.3 RAW/HEIC/Video Edge Coverage

- Camera vendor sample packs (RAW/HEIC)
- Public codec test clips for video compatibility

---

## 4) Repository Data Layout

```text
tests/
  fixtures/
    unit/
      images/
      videos/
      raw/
      heic/
      invalid/
    integration/
      manifests/
        small.yaml
        medium.yaml
        target.yaml
      datasets/   # local cache, gitignored
```

Each manifest should include:

- relative path
- media type
- expected ingest support (true/false)
- expected derivative/proxy requirement
- expected metadata minimums
- optional face labels (where legally permitted)

---

## 5) FR/NFR Coverage Mapping

## 5.1 Batch A (FR-001..005, FR-017..022, FR-043..046)

- Tier 0 for deterministic TDD loops
- Tier 1 for acceptance confirmation

## 5.2 Batch B (FR-006..016, FR-023..028)

- Tier 1 required
- Tier 0 only for isolated failure-path unit tests

## 5.3 Batch C (FR-033..042, FR-047..050)

- Tier 1 integration validation

## 5.4 Batch D (NFR-001..015)

- Tier 2 required
- Record hardware and dataset profile per run

---

## 6) Dataset Profiles for Execution

- **Small**: 200–500 assets (developer fast checks)
- **Medium**: 2,000–5,000 assets (pre-merge integration)
- **Target**: 20,000+ assets (release/perf gate)

Suggested media composition for medium/target profiles:

- 70–80% JPG/PNG
- 5–10% RAW
- 5–10% HEIC
- 5–10% video
- 1–2% known-bad/corrupt files

---

## 7) TDD (Red-Green-Refactor) Dataset Workflow

For each requirement slice:

1. Select fixture subset from manifest
2. Write failing test(s) against requirement behavior (RED)
3. Implement minimum behavior to pass (GREEN)
4. Refactor while preserving passing tests (REFACTOR)
5. Validate with formatter/lint/tests
6. Promote from Tier 0 checks to Tier 1 acceptance before merge

This keeps requirement-defined behavior as the source of truth and minimizes drift.

---

## 8) Governance, Compliance, and Reproducibility

- Do not commit large datasets to git
- Track dataset provenance and license metadata
- Maintain reproducible manifests with stable IDs/checksums where feasible
- Add face-data handling notes aligned with privacy/deletion requirements (FR-028, NFR-014)
- Keep benchmark runs traceable to environment profile (CPU/RAM/Linux distro)

---

## 9) First Implementation Slice Recommendation

Start with **FR-001..005** using Tier 0 fixtures:

- schema init + version check
- scanner behavior for supported/unsupported files
- incremental fingerprint logic + force mode
- failure capture and run summary accounting

Then rerun equivalent integration checks on Tier 1 (small/medium profile).
