# Implementation Plan: CLI Service Lifecycle (FR-042)

**Branch**: `feature/fr-042-cli-lifecycle`
**Scope**: FR-042 (CLI start/stop/restart + unified process-new pipeline)

## Stage 1: Service lifecycle commands (start/stop/restart)

**Goal**: `rapidcull start/stop/restart` with PID-file management and actionable diagnostics

**Success Criteria**:
- `rapidcull start [--host] [--port] [--pid-file]` launches uvicorn background process, writes PID file
- `rapidcull stop [--pid-file]` kills process by PID, removes PID file
- `rapidcull restart` = stop (if running) + start
- Error messages: "already running (PID=N)", "port N already in use", "no running service found"
- `click>=8.0.0` in `[project.optional-dependencies] cli`
- `[project.scripts] rapidcull = "rapidcull.cli:main"` in pyproject.toml

**Tests**: `tests/integration/cli/test_cli_service.py`
- start creates PID file
- start when already running prints error, exits nonzero
- start when port in use prints error, exits nonzero
- stop kills process and removes PID file
- stop when no PID file prints error
- stale PID file (process dead) cleaned up gracefully
- restart invokes stop then start

**Status**: In Progress

---

## Stage 2: process-new pipeline command

**Goal**: `rapidcull process-new --source-dir DIR` runs discover → plan → ingest → proxy → summary

**Success Criteria**:
- Discovers supported media in source-dir recursively
- Runs metadata extraction (ExifTool) and proxy generation
- Prints: `Processed: N | Skipped: N | Failed: N`
- source-dir must exist; actionable error if not

**Tests**: `tests/integration/cli/test_cli_process_new.py`
- happy path with mocked adapters reports correct counts
- empty source-dir reports 0|0|0
- missing source-dir exits nonzero with message
- failed extraction items appear in failed count

**Status**: Not Started

---

## Stage 3: Quality gates

**Goal**: All gates green
**Success Criteria**: `black`, `ruff`, `mypy --strict src/rapidcull`, `pytest` all pass
**Status**: Not Started
