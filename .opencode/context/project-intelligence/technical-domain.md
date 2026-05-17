<!-- Context: project-intelligence/technical | Priority: high | Version: 2.0 | Updated: 2026-03-27 -->

# Technical Domain

> Document the technical foundation, architecture, and key decisions for RapidCull.

## Quick Reference

- **Purpose**: Understand how RapidCull works technically today and where it is headed
- **Update When**: New pipeline features land, architecture changes, external toolchain changes, or local/dev workflow changes
- **Audience**: Developers, technical stakeholders, future agents

## Primary Stack

| Layer | Technology | Version | Rationale |
|-------|-----------|---------|-----------|
| Language | Python | 3.11+ | Strong typing, stdlib filesystem/subprocess support, and good fit for local pipeline orchestration |
| Application Shape | Modular Python package | Current repo shape | Keeps ingest, proxy, and gallery logic focused without premature service sprawl |
| Database | SQLite | Project requirement / stdlib | Lightweight local canonical store for metadata and schema-managed state |
| Media/Metadata Toolchain | ExifTool, FFmpeg, ImageMagick, RawTherapee CLI | System-installed | Mature Linux-native tools for metadata extraction and derivative generation |
| Quality/Test Tooling | pytest, pytest-cov, pytest-xdist, pytest-benchmark, Playwright, black, ruff, mypy | See `pyproject.toml` | Enforces deterministic behavior, strict typing, validation gates, and browser/UI test capability |
| Planned Domain Libraries | numpy, opencv-python, pillow, scikit-learn, insightface, onnxruntime | Target runtime stack | Supports image processing, computer vision, and face-recognition workflows |

## Architecture Pattern

```text
Type: Modular local-first monolith
Pattern: Filesystem-driven media pipeline with typed domain models and external-tool adapters
Diagram: None yet
```

### Why This Architecture?

RapidCull is a **Linux-first, local-first** toolkit for large media libraries. That drives a few core choices:

- Keep media on the local filesystem rather than behind remote storage abstractions
- Use mature external tools for metadata extraction and derivative generation instead of reimplementing them in Python
- Keep orchestration, validation, accounting, and summaries in Python where behavior is easier to type-check and test
- Favor narrow modules and requirement-mapped integration tests over framework-heavy architecture

This architecture fits the product goals: offline/local usage, deterministic processing, continue-on-error batch behavior, and safe handling of large photo/video libraries.

## Project Structure

```text
[Project Root]
├── src/rapidcull/            # Application/domain code
├── tests/                    # Unit, integration, UI, and NFR tests
├── docs/                     # Requirements, plans, dependencies, lessons learned
├── scripts/                  # Bootstrap and system dependency verification
├── infra/                    # Container/sandbox-related assets
└── .opencode/context/        # Project intelligence, standards, workflows
```

**Key Directories**:
- `src/rapidcull/` - Core application logic, including ingest, metadata extraction adapters, proxy generation, gallery lifecycle code, and typed models
- `tests/` - Requirement-oriented coverage with strong integration emphasis for ingest, proxy, and gallery behavior
- `docs/` - Product requirements, acceptance/testing plans, dependency inventory, and lessons learned
- `scripts/` - Local setup and Linux system dependency verification
- `.opencode/context/` - Project standards, technical/business context, and workflow guidance

## Key Technical Decisions

| Decision | Rationale | Impact |
|----------|-----------|--------|
| Python 3.11+ baseline | Matches current project metadata and strict typing/tooling expectations | Avoids environment drift and supports consistent local validation |
| Linux-only support | Simplifies media-tool integration and reduces platform variability | Faster iteration, but no cross-platform portability baseline |
| External-tool adapters for metadata/proxies | ExifTool, FFmpeg, ImageMagick, and RawTherapee are better suited than custom reimplementation | Requires explicit preflight checks and normalized error taxonomy |
| SQLite + JSON + filesystem consistency model | DB stores canonical metadata, JSON supports UI/cache artifacts, filesystem remains media truth | Clear separation of concerns across durable state, derived state, and source media |
| Deterministic result contracts | Stable ordering, summaries, and reason codes make behavior testable and predictable | Improves operator trust and reduces flaky integration coverage |
| Continue-on-error batch processing | Large library runs should complete as far as possible despite partial failures | Requires per-item failure reasons and final summary accounting |

See `decisions-log.md` for fuller decision history and rationale.

## Integration Points

| System | Purpose | Protocol / Mechanism | Direction |
|--------|---------|----------------------|-----------|
| Local filesystem | Source of truth for media assets and gallery files | Native file I/O | Inbound + internal |
| SQLite | Canonical metadata/state store | Python DB access | Internal |
| ExifTool | Batch metadata extraction during ingest | Safe subprocess invocation | Outbound |
| ImageMagick | Still-image and HEIC proxy generation | Safe subprocess invocation | Outbound |
| RawTherapee CLI | RAW-to-display proxy generation | Safe subprocess invocation | Outbound |
| FFmpeg | Video proxy generation/transcoding | Safe subprocess invocation | Outbound |
| Future local/LAN API surface | UI/API orchestration and jobs | Planned versioned HTTP API | Inbound |

## Technical Constraints

| Constraint | Origin | Impact |
|------------|--------|--------|
| Python >=3.11 required | `pyproject.toml` and tooling | Local setup breaks or drifts under 3.10 |
| Linux-first only | Product scope | OS-specific toolchain assumptions are acceptable |
| ImageMagick must include HEIC/HEIF capability | FR-007 requirements | HEIC workflows should fail fast with actionable diagnostics if unsupported |
| External tools must use validated normalized paths | Security requirements | No shell interpolation of user-provided values |
| Deterministic summaries and reason taxonomies | FR/NFR contracts | Sorting, normalization, and explicit accounting matter |
| Continue-on-error pipeline behavior | Product behavior | Pipelines should report partial failure rather than abort entire runs |
| Large-library performance targets | Product/NFR goals | Design should support adaptive parallelism and efficient derivative workflows |

## Development Environment

```text
Setup:
  ./scripts/bootstrap.sh

Verify system dependencies:
  ./scripts/verify_system_deps.sh

Requirements:
  - Python 3.11+
  - venv
  - ExifTool
  - FFmpeg
  - ImageMagick with HEIC/HEIF support
  - RawTherapee CLI

Local validation:
  .venv/bin/python -m pytest
  .venv/bin/python -m black --check .
  .venv/bin/python -m ruff check .
  .venv/bin/python -m mypy src
```

### Development Notes

- Prefer interpreter-bound commands such as `.venv/bin/python -m pytest` to avoid PATH/venv drift
- Keep bootstrap instructions aligned with `pyproject.toml` and the dependency catalog
- Treat system media-tool checks as part of development readiness, not post-failure cleanup

## Deployment and Runtime Posture

```text
Current State:
  Local development / local execution focus

Target Modes:
  - localhost-only mode
  - LAN mode

CI/CD:
  No checked-in CI workflow detected currently

Observability Direction:
  Structured logs, run summaries, and job status reporting are requirement-level expectations
```

RapidCull is currently documented as a local/self-hosted toolkit rather than a cloud-first service.

## Current Technical State

- The repository has moved beyond pure scaffolding; multiple ingest, proxy, and gallery slices are documented as completed in `living-notes.md`
- Current implementation emphasis is on deterministic pipeline behavior, typed models, and requirement-mapped integration coverage
- Face-recognition, API surface, and broader orchestration capabilities are present in requirements and dependency planning, but not all are necessarily implemented yet
- The technical documentation should distinguish clearly between **current implementation** and **target product direction**

## Onboarding Checklist

- [ ] Know the Python 3.11+ baseline and strict tooling gates
- [ ] Understand the local-first filesystem + SQLite + JSON consistency model
- [ ] Know which external tools are required and why
- [ ] Understand the modular monolith and adapter-based architecture
- [ ] Know where ingest, proxy, gallery, and model code live
- [ ] Be able to bootstrap the environment and verify system dependencies
- [ ] Know that deterministic summaries and continue-on-error behavior are core contracts
- [ ] Understand the difference between current implementation state and planned future capabilities

## Related Files

- `business-domain.md` - Why this technical foundation exists
- `business-tech-bridge.md` - How product needs map to this architecture
- `decisions-log.md` - Decision history and rationale
- `living-notes.md` - Current issues, debt, and active implementation slices
- `../../../docs/20260307T080227--photo-library-requirements__projects.md` - Functional and non-functional requirements
- `../../../docs/20260307T093000--rapidcull-dependencies__projects.md` - Dependency inventory and verification expectations
- `../../../pyproject.toml` - Current Python and tooling configuration
