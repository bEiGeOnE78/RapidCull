<!-- Context: project-intelligence/business | Priority: high | Version: 2.0 | Updated: 2026-03-27 -->

# Business Domain

> Document the product context, user problems, and value RapidCull is meant to create.

## Quick Reference

- **Purpose**: Understand why RapidCull exists and what outcomes it is trying to deliver
- **Update When**: Product scope changes, target users shift, roadmap direction changes, or major capabilities ship
- **Audience**: Developers, stakeholders, future agents, product/technical owners

## Project Identity

```text
Project Name: RapidCull
Tagline: Linux-first, local-first photo library ingestion, culling, and organization toolkit
Problem Statement: Large local photo/video libraries are hard to ingest, browse, cull, organize, and maintain quickly without giving up control to cloud-first systems
Solution: Provide a self-hosted/local workflow for ingest, metadata extraction, proxy generation, galleries, culling, and face-assisted organization
```

## Target Users

| User Segment | Who They Are | What They Need | Pain Points |
|--------------|--------------|----------------|-------------|
| Primary | Photographer or advanced hobbyist with a large local library | Fast ingest, browsing, culling, and organization across mixed media types | Slow tools, inconsistent metadata, manual sorting, weak support for RAW/HEIC/video mixes |
| Secondary | Self-hosting or local power user | Private, controllable media workflows on local Linux hardware | Cloud lock-in, opaque processing, limited control, privacy concerns |
| Future / Shared Use | Small LAN-based household or team operator | Shared access with safe mutating controls and predictable behavior | Need for light access control and operational clarity without full SaaS complexity |

## Value Proposition

**For Users**:
- Fast local workflows for ingest, culling, and browsing
- Privacy-preserving organization without requiring cloud upload
- Safe handling of originals while working from derived artifacts and virtual galleries
- Support for real-world mixed media libraries: stills, RAW, HEIC, and video
- Operator-visible summaries and actionable failure reporting

**For the Product**:
- Clear differentiation through local-first, Linux-first workflows
- Strong fit for users who value control, speed, and privacy over hosted convenience
- Expandable foundation for query, API, jobs, and face-recognition features

## Success Metrics

| Metric | Definition | Target | Current |
|--------|------------|--------|---------|
| Gallery open time | Cached gallery open latency | < 1.5s p95 | Requirement target |
| Image switch speed | Next/prev perceived latency with preloading | < 100ms p95 | Requirement target |
| UI command feedback | Time from action to visible feedback for non-IO actions | < 50ms p95 | Requirement target |
| Pipeline resilience | Processing continues despite per-item/tool failures | Continue-on-error with summaries | Core product contract |
| Operator clarity | Run results include processed/skipped/failed counts and reasons | Deterministic, actionable summaries | Core product contract |

## Product Positioning

```text
Deployment Model: Localhost-first, with optional LAN mode
Auth Model: No auth by default in localhost mode; token/password required in LAN mode
Privacy Position: User-controlled, local-first, explicit deletion/retention for sensitive data like face records
Market Position: Power-user/self-hosted media management toolkit, not a cloud multi-tenant platform
```

## Ownership

| Role | Responsibility |
|------|----------------|
| Product / Requirements Owner | Defines scope, functional/non-functional requirements, and priorities |
| Technical Lead / Engineering | Owns architecture, implementation direction, and validation quality |
| Maintainers | Keep project-intelligence, lessons learned, and current-state docs up to date |

## Roadmap Context

**Current Focus**: Ingest, metadata extraction, proxy generation, and gallery-lifecycle foundations with deterministic behavior and strong test coverage  
**Next Milestone**: Query grammar, API/job orchestration, and broader end-user workflow completion  
**Long-term Vision**: A fast, privacy-respecting, self-hosted media-management workspace for large local libraries

## Business Constraints

- **Linux only** - simplifies tooling and support scope
- **Local/self-hosted first** - cloud multi-tenant behavior is out of scope
- **Large-library performance matters** - UX speed and deterministic processing are part of the value proposition
- **Original media safety matters** - workflows must avoid unsafe mutation of masters
- **Privacy matters** - face data retention/deletion must remain user-controlled
- **Operational clarity matters** - long-running work must surface progress and actionable summaries

## Onboarding Checklist

- [ ] Understand the problem RapidCull is solving
- [ ] Know the primary user segments and their pain points
- [ ] Understand why local-first and Linux-first are strategic choices
- [ ] Know the product value proposition and success criteria
- [ ] Understand current roadmap focus vs long-term direction
- [ ] Know the major business constraints shaping technical choices

## Related Files

- `technical-domain.md` - How this product need is solved technically
- `business-tech-bridge.md` - Mapping between business and technical decisions
- `decisions-log.md` - Decision index for product-shaping choices
- `decisions/navigation.md` - Topic-based decision discovery
- `living-notes.md` - Current state, open questions, and active pressure
