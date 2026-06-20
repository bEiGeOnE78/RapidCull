# RapidCull User Guide

## Overview

RapidCull is a local-first photo library toolkit for Linux. It ingests media from your filesystem, generates display proxies, and provides a browser-based interface for browsing, culling, and organizing large collections without cloud upload.

All media stays on your machine. The database and derived artifacts live alongside your library. Source files are never modified.

---

## System Requirements

- Linux (primary supported platform)
- Python 3.11 or later
- ExifTool (metadata extraction)
- FFmpeg (video and proxy generation)
- ImageMagick with HEIC/HEIF support (proxy generation for stills)
- RawTherapee CLI (optional — required for RAW format support)

Verify system dependencies:

```bash
./scripts/verify_system_deps.sh
```

---

## Installation

```bash
git clone <repo-url>
cd RapidCull
./scripts/bootstrap.sh
```

The bootstrap script creates a `.venv` virtual environment and installs all Python dependencies. It requires Python 3.11+. If your system default is older, install Python 3.11 via pyenv first and ensure it is active before running bootstrap.

After bootstrapping, activate the environment:

```bash
source .venv/bin/activate
```

---

## Starting the Server

```bash
rapidcull start --db ~/photos/rapidcull.db --library-root ~/photos
```

This starts the API server on `http://127.0.0.1:8000` as a background process and writes a PID file to `~/.local/run/rapidcull/rapidcull.pid`.

Options:

| Flag | Default | Description |
|------|---------|-------------|
| `--host` | `127.0.0.1` | Host to bind to |
| `--port` | `8000` | Port to bind to |
| `--db` | none | Path to `rapidcull.db` (created if missing) |
| `--library-root` | none | Root directory for the photo library |
| `--pid-file` | `~/.local/run/rapidcull/rapidcull.pid` | Path to PID file |

Verify the server is running:

```bash
curl http://127.0.0.1:8000/api/v1/jobs
```

Stop the server:

```bash
rapidcull stop
```

Restart (stop then start):

```bash
rapidcull restart --db ~/photos/rapidcull.db --library-root ~/photos
```

Open `http://127.0.0.1:8000` in a browser to access the UI.

---

## Ingesting Your Library

Ingest scans for new media, extracts metadata via ExifTool, stores image records in the database, and generates display proxies.

### Via CLI

```bash
rapidcull process-new --source-dir /path/to/photos
```

Options:

| Flag | Default | Description |
|------|---------|-------------|
| `--source-dir` | (required) | Directory to scan for new media |
| `--raw-pipeline` / `--no-raw-pipeline` | enabled | Enable or disable RAW processing |

Output reports a summary line:

```
Processed: 142 | Skipped: 3 | Failed: 0
```

- **Processed**: new files imported and proxied
- **Skipped**: files already in the database
- **Failed**: files that could not be processed (metadata or proxy errors)

### Via Web UI

Open the command palette (`/` key), select **Process new images**, and confirm. A progress panel appears showing live log output.

### Supported Formats

| Category | Extensions |
|----------|-----------|
| JPEG | `.jpg`, `.jpeg` |
| PNG | `.png` |
| HEIC/HEIF | `.heic`, `.heif` |
| RAW | `.cr2`, `.cr3`, `.nef`, `.arw`, `.dng`, `.orf`, `.rw2` |
| Video | `.mp4`, `.mov`, `.mkv`, `.avi` |

Ingest is continue-on-error: a failure on one file does not stop the run. Failed files are counted and their reasons recorded.

---

## Browsing Images

After starting the server and ingesting media, open the UI at `http://127.0.0.1:8000`.

The main view consists of:

- **Gallery sidebar** (left): lists all available galleries. Toggle with `G` or the Galleries button.
- **Thumbnail grid** (center): shows images in the selected gallery, 50 per page.
- **Image viewer** (overlay): opens when you click a thumbnail. Shows the full display proxy with culling controls.

### Sorting

The thumbnail grid can be sorted by filename, date ascending, date descending, picks first, rejects first, or undecided first using the sort control above the grid.

### Pagination

Use the page controls below the grid to move between pages. Each page shows up to 50 images.

---

## Culling Images

Open an image by clicking its thumbnail. The image viewer shows the display proxy with the filename, position in set, and decision controls.

### Decisions

| Action | Key | Button | Effect |
|--------|-----|--------|--------|
| Pick | `P` | PICK | Mark image as a keeper |
| Reject | `X` | REJECT | Mark image for removal |
| Undo | — | UNDO | Clear the current decision |

Pressing `P` when an image is already picked clears the pick (toggle). Pressing `X` when an image is already rejected clears the reject (toggle). The UNDO button is disabled when there is no decision.

Decision state is visible in the viewer:
- Green border and green PICK button: picked
- Red border, red tint overlay, and red REJECT button: rejected
- No border: undecided

---

## The Trash Workflow

Rejecting an image does not remove it from the library immediately. RapidCull uses a two-step deletion workflow.

### Step 1 — Reject

Mark images as rejected in the viewer (`X`). Rejected images remain in the library and are visible in the grid.

### Step 2 — Move rejects to trash

Open the command palette (`/`), select **Move rejects to trash**, and confirm. All images with a reject decision are moved to a `.trash/` directory inside the library root. Their records are updated in the database. This is a soft delete — the files are recoverable.

### Recovering from trash

Open the **Trash** panel (Trash button in the header). Trashed items are listed there. Individual items can be restored, which moves the file back and reinstates its database record.

### Step 3 — Hard delete

Open the command palette (`/`), select **Hard delete trash**, and confirm the destructive action dialog. All items currently in trash are permanently deleted from disk. This cannot be undone.

---

## Creating Galleries

A gallery is a named collection of images stored as hardlinks under `<library-root>/galleries/`. Hardlinks avoid media duplication — no files are copied.

### Create a gallery from picks

Open the command palette (`/`) and select **Create gallery from picks**. This creates a gallery containing all images currently marked as picked.

### Rebuild the galleries index

If you have manually modified the galleries directory or after a first-time setup, run **Rebuild galleries index** from the command palette to refresh the gallery list in the UI.

---

## Face Recognition & Person Management

Face recognition runs as two sequential background jobs.

### Step 1 — Detect faces

Open the command palette (`/`) and select **Detect faces**. This runs InsightFace detection across all images in the database, storing face bounding boxes and embeddings.

### Step 2 — Cluster faces

Select **Cluster faces** from the command palette. This groups face embeddings into person identities using DBSCAN clustering. After clustering, unnamed clusters appear as "Person 1", "Person 2", etc. in the People panel.

### Managing persons

Open the **People** panel (People button in the header) to view all detected persons. From there you can rename a person or merge two person records into one.

### Face overlay in the viewer

While viewing an image, press `O` to toggle the face overlay. Detected faces appear as labeled bounding boxes over the image.

---

## Background Jobs

All long-running operations run as background jobs. The job progress panel appears automatically when a job is started from the command palette.

### Job kinds

| Kind | Description |
|------|-------------|
| `ingest_and_proxy` | Scan library root, import new images, generate proxies |
| `detect_faces` | Run face detection on all images in the database |
| `cluster_faces` | Cluster face embeddings into person identities |
| `create_gallery_picks` | Create a gallery from all currently picked images |
| `move_rejects_to_trash` | Move all rejected images to the `.trash/` directory |
| `hard_delete_trash` | Permanently delete all items in trash |
| `rebuild_galleries_index` | Rebuild the gallery metadata index from disk |
| `backup` | Back up the database and gallery JSON state to a timestamped directory |
| `check_consistency` | Verify the database and filesystem are in sync |
| `repair_consistency` | Fix detected consistency issues |

Jobs run one at a time in a single background thread. Submitting a second job while one is running queues it.

### Checking job status via API

```bash
# List all jobs
curl http://127.0.0.1:8000/api/v1/jobs

# Get a specific job and its progress log
curl http://127.0.0.1:8000/api/v1/jobs/<job-id>
curl http://127.0.0.1:8000/api/v1/jobs/<job-id>/progress
```

### Consistency check and repair (CLI)

```bash
# Check only
rapidcull check --db ~/photos/rapidcull.db

# Check and repair
rapidcull check --db ~/photos/rapidcull.db --repair --confirmed
```

### Backup and restore (CLI)

```bash
# Backup
rapidcull backup --db ~/photos/rapidcull.db --backup-root ~/photos/backups

# Restore (overwrites existing data)
rapidcull restore --backup-path ~/photos/backups/20260614T120000 \
  --db ~/photos/rapidcull.db --confirmed
```

---

## Keyboard Shortcuts

Shortcuts are active when focus is not in a text input, textarea, or select element.

### Global (thumbnail grid view)

| Key | Action |
|-----|--------|
| `G` | Toggle gallery sidebar |
| `/` | Open command palette |

### Image viewer

| Key | Action |
|-----|--------|
| `ArrowLeft` | Previous image |
| `ArrowRight` | Next image |
| `P` | Pick (toggle) |
| `X` | Reject (toggle) |
| `Space` | Toggle zoom / fit mode |
| `M` | Toggle metadata sidebar |
| `O` | Toggle face overlay |
| `Q` | Close viewer |
| `Escape` | Close viewer |

### Command palette

| Key | Action |
|-----|--------|
| `ArrowUp` / `ArrowDown` | Navigate commands |
| `Enter` | Run selected command |
| `Escape` | Close palette |

---

## Query Language

RapidCull's query language filters images by metadata fields. Queries are used when building collection views or virtual galleries.

Full reference: [`docs/query-grammar.md`](query-grammar.md)

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `person` | text (multi-value) | Recognized person name |
| `date` | date (`YYYY-MM-DD`) | Capture date |
| `camera` | text | Camera body model |
| `lens` | text | Lens model |
| `iso` | integer | ISO sensitivity |
| `fnumber` | number | Aperture f-number |
| `focal` | number | Focal length in mm |
| `keyword` | text (multi-value) | Keyword tag |

### Operators

Text fields (`person`, `camera`, `lens`, `keyword`): `=`, `!=`, `~` (substring match)

Ordered fields (`date`, `iso`, `fnumber`, `focal`): `=`, `!=`, `>`, `>=`, `<`, `<=`

### Boolean logic

Combine expressions with `AND`, `OR`, `NOT` (case-insensitive). Use parentheses to control evaluation order. Precedence: `NOT` > `AND` > `OR`.

### Examples

```
# Images of a specific person
person=alice

# Images from a date range
date>=2024-01-01 AND date<2025-01-01

# Low-noise shots
iso<=400

# Wide-aperture portraits
fnumber<=2.8 AND keyword=portrait

# Either of two people, excluding blurred shots
(person=alice OR person=bob) AND NOT keyword=blurred

# Specific camera body
camera=Leica Q2

# Any Canon camera, fast glass, portrait keyword
camera~Canon AND fnumber<=1.8 AND keyword=portrait
```

Missing fields evaluate as non-match. Invalid queries return a structured error with a code, message, and suggestions.
