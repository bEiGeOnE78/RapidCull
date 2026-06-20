# RapidCull

Linux-first, local-first photo library ingestion, culling, face-assisted organization, and gallery creation toolkit.

## Quick Start

**1. Install**

```bash
git clone <repo>
cd RapidCull
./scripts/bootstrap.sh
```

**2. Start the server**

```bash
rapidcull start --db ~/photos/rapidcull.db --library-root ~/photos
```

Opens the web UI at http://127.0.0.1:8000

**3. Use the web UI**

- Press `/` to open the command palette → run **Ingest & Proxy** to scan your library
- Browse galleries in the left sidebar (press `G` to toggle)
- Pick/reject images with `P` / `R` — or click the green/red badges
- Open the command palette → move rejects to trash → hard delete when ready

**4. Stop**

```bash
rapidcull stop
```

## Documentation

- [User Guide](docs/user-guide.md) — Full workflow walkthrough, UI reference, keyboard shortcuts
- [CLI Reference](docs/cli-reference.md) — All commands with full option details and examples
- [API Reference](docs/api-reference.md) — REST endpoints with request/response schemas and error codes
- [Query Language](docs/query-grammar.md) — Filter expression reference for galleries and collections
- [Query Recipes](docs/query-recipes.md) — 20+ ready-to-use query patterns
- [Operations Guide](docs/ops-guide.md) — Backup, restore, troubleshooting, environment variables

## CLI Reference

| Command | Description |
|---------|-------------|
| `rapidcull start [--db PATH] [--library-root PATH] [--host H] [--port N]` | Start API server |
| `rapidcull stop` | Stop API server |
| `rapidcull restart [--db PATH] [--library-root PATH]` | Restart API server |
| `rapidcull process-new --source-dir PATH` | Ingest new media from directory |
| `rapidcull backup --db PATH --backup-root PATH` | Backup DB and gallery state |
| `rapidcull restore --backup-path PATH --db PATH --confirmed` | Restore from backup |
| `rapidcull check --db PATH [--repair --confirmed]` | Check/repair DB-FS consistency |

## API

The server exposes a REST API at `/api/v1/`. FastAPI interactive docs: http://127.0.0.1:8000/docs

## Query Language

See [docs/query-grammar.md](docs/query-grammar.md) for the query expression reference used in collection search and gallery creation.

## System Requirements

- Python 3.11+
- ExifTool
- FFmpeg
- ImageMagick with HEIC/HEIF support
- RawTherapee CLI (optional, for RAW file processing)

## Development

```bash
./scripts/bootstrap.sh           # create venv + install deps
.venv/bin/python -m pytest       # run test suite
.venv/bin/python -m mypy src     # type check
cd frontend && npm run dev       # frontend dev server (proxies API to :8000)
```
