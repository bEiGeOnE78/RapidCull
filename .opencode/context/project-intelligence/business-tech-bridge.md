<!-- Context: project-intelligence/bridge | Priority: high | Version: 2.0 | Updated: 2026-03-27 -->

# Business ↔ Tech Bridge

> Show how RapidCull's product goals translate into technical architecture, contracts, and constraints.

## Quick Reference

- **Purpose**: Explain why the technical design exists in business terms
- **Update When**: Product priorities shift, a major capability lands, or a cross-cutting technical choice changes
- **Audience**: Product owners, developers, maintainers, future agents

## Core Mapping

| Business Need | Technical Solution | Why This Mapping | Business Value |
|---------------|-------------------|------------------|----------------|
| Fast local workflows for large libraries | Local filesystem-first architecture, SQLite metadata, JSON derived artifacts, proxy generation | Large media libraries are too slow and heavy to manage directly from originals alone | Faster browsing, culling, and organization without cloud dependence |
| Mixed-media support | ExifTool, ImageMagick, RawTherapee, and FFmpeg behind adapter seams | Mature external tools cover metadata, stills, RAW, HEIC, and video workflows better than early custom reimplementation | Broader format coverage with less reinvention risk |
| Privacy and user control | Local/self-hosted posture, localhost/LAN modes, explicit data-retention expectations | Users who value control and privacy need workflows that do not require cloud upload | Stronger trust and better fit for self-hosted/power-user workflows |
| Safe handling of originals | Hard-link galleries, derived artifacts, validated path handling, allowlist mutation boundaries | Organization and culling must not put master files at risk | Safer workflows with lower storage overhead and less accidental damage |
| Useful output from long-running jobs | Continue-on-error pipelines, deterministic summaries, per-item failure reporting | Large runs should remain valuable even when some assets fail | Better operator trust and less all-or-nothing frustration |

## Current High-Value Mappings

### Ingest and metadata foundation

**Business Context**:
- Users need to turn large, messy local libraries into structured, usable media catalogs
- Manual metadata handling does not scale across mixed still/video libraries

**Technical Implementation**:
- Scan configured library roots
- Extract media metadata with ExifTool, including persistent batch-mode support
- Normalize metadata into canonical fields used across storage and outputs

**Connection**:
This turns unstructured local media into a consistent foundation for browsing, filtering, culling, and later automation without forcing users into a hosted system.

### Proxy generation for responsive browsing

**Business Context**:
- Users need a fast browsing/culling experience even when originals are RAW, HEIC, or video
- Originals are too large, slow, or browser-unfriendly for direct UI use

**Technical Implementation**:
- Still-image proxy generation via ImageMagick
- RAW proxy generation via RawTherapee CLI
- Video proxy generation via FFmpeg
- Derived proxies instead of mutating original media

**Connection**:
Responsive derived assets make the product usable at library scale while preserving the original files users care most about.

### Gallery lifecycle without master-file mutation

**Business Context**:
- Users need lightweight organization workflows that do not duplicate or damage originals
- Curated sets, picks, and selections need to remain operationally simple

**Technical Implementation**:
- Virtual galleries created via hard links
- Deterministic gallery metadata and index rebuilds
- Allowlist-based rename/delete controls for gallery mutations

**Connection**:
This gives users flexible organization and curation while keeping storage overhead low and safety expectations high.

### Reliability and operator trust

**Business Context**:
- Large ingest/proxy runs should still produce useful output when a subset of files fail
- Operators need clear signals about what happened and what needs attention

**Technical Implementation**:
- Continue-on-error pipeline behavior
- Stable processed/skipped/failed accounting
- Canonical reason taxonomy and deterministic summaries

**Connection**:
Operators get actionable output instead of all-or-nothing failure, which matters more in large real-world libraries than idealized perfect runs.

## Target / Next-Phase Mappings

| Product Direction | Likely Technical Direction | Why It Matters |
|-------------------|----------------------------|----------------|
| Structured query workflows | Query grammar, validation, and indexed metadata access | Makes large libraries explorable without manual folder-only organization |
| UI/API orchestration | Versioned `/api/v1` endpoints and job-state model | Supports richer user flows and long-running task visibility |
| Face-assisted organization | Embedding, clustering, naming, and deletion workflows | Extends organization speed while preserving user control over sensitive data |
| Adaptive throughput | Configurable parallel workers with deterministic accounting | Improves performance without sacrificing trust in output summaries |

## Trade-off Decisions

| Situation | Business Priority | Technical Priority | Decision Made | Rationale |
|-----------|-------------------|-------------------|---------------|-----------|
| Local control vs hosted convenience | Privacy, control, offline/local usability | Simpler architecture and predictable local dependencies | Local/self-hosted first | Best fit for the intended users and current scope |
| Broader platform support vs faster delivery | Reach more users | Reduce environment/toolchain variability | Linux-only baseline | Enables faster, more reliable delivery in the current phase |
| Fast feature coverage vs pure in-house implementation | Support real media formats quickly | Avoid unnecessary reinvention | Use mature external media tools | Delivers more capability sooner with explicit adapter boundaries |
| Simpler failure model vs useful large-run output | Keep long runs valuable | Preserve contract clarity | Continue-on-error with summaries | Better fit for real-world batch workflows |

## Common Misalignments to Watch

| Misalignment | Warning Signs | Resolution Approach |
|--------------|---------------|---------------------|
| Convenience shortcuts weaken safety goals | Skipping path validation or broadening mutation scope casually | Re-anchor changes to original-safety and local-trust requirements |
| Fail-fast behavior sneaks into pipeline flows | One bad asset/tool aborts otherwise useful batch work | Preserve continue-on-error unless product policy explicitly changes |
| Technical implementation overstates product maturity | Docs imply API/face workflows are fully landed when they are still roadmap items | Mark current-state vs target-state clearly |
| Tooling changes ignore user-facing value | Refactors optimize internals but reduce determinism or summary clarity | Keep operator trust and product contracts as acceptance criteria |

## Onboarding Checklist

- [ ] Understand the major product promises RapidCull makes to users
- [ ] Know how local-first, privacy, and safety goals shape architecture
- [ ] See how ingest, proxies, galleries, and reporting map to user value
- [ ] Understand the main trade-offs accepted by the project
- [ ] Be able to explain why the technical constraints exist in product terms

## Related Files

- `business-domain.md` - Business needs and user value in detail
- `technical-domain.md` - Technical implementation and constraints in detail
- `decisions-log.md` - Decision index for major choices
- `decisions/navigation.md` - Topic-based decision discovery
- `decisions/architecture.md` - Product posture and state-model choices
- `decisions/pipeline-contracts.md` - Behavior contracts that protect user value
- `decisions/security-operations.md` - Safety choices tied to trust and operational boundaries
- `living-notes.md` - Current pressure, open questions, and implementation status
