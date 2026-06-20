# RapidCull CLI Reference

## Installation & Setup

Activate the project virtual environment before running any commands:

```sh
source .venv/bin/activate
rapidcull --help
```

Or use the full path without activating:

```sh
.venv/bin/rapidcull --help
```

---

## Commands

### `rapidcull start`

Start the RapidCull API server as a background process. Writes a PID file so the server can be stopped later. Exits with an error if the server is already running or if the target port is already in use.

**Options**

| Option | Type | Default | Required | Description |
|---|---|---|---|---|
| `--host` | string | `127.0.0.1` | No | Host address to bind the server to |
| `--port` | integer | `8000` | No | Port to bind the server to |
| `--pid-file` | path | `~/.local/run/rapidcull/rapidcull.pid` | No | Path to the PID file written on startup |
| `--db` | path | None | No | Path to `rapidcull.db`; creates the file if missing. Sets `RAPIDCULL_DB_PATH` in the server environment |
| `--library-root` | path | None | No | Root directory for the photo library. Sets `RAPIDCULL_LIBRARY_ROOT` in the server environment |

**Examples**

```sh
# Start with defaults (127.0.0.1:8000)
rapidcull start

# Bind to all interfaces on a custom port
rapidcull start --host 0.0.0.0 --port 9000

# Point at a specific database and library root
rapidcull start --db /data/rapidcull.db --library-root /mnt/photos
```

**Notes**

- `--db` and `--library-root` are passed to the server process as environment variables, not as command-line flags to uvicorn. They take effect at server startup and cannot be changed without a restart.
- The PID file directory is created automatically if it does not exist.

---

### `rapidcull stop`

Stop a running RapidCull API server. Sends `SIGTERM` and waits up to 5 seconds for graceful shutdown. If the process is still alive after that window, sends `SIGKILL`. Removes the PID file on success.

**Options**

| Option | Type | Default | Required | Description |
|---|---|---|---|---|
| `--pid-file` | path | `~/.local/run/rapidcull/rapidcull.pid` | No | Path to the PID file written by `start` |

**Examples**

```sh
# Stop the default server instance
rapidcull stop

# Stop a server started with a custom PID file
rapidcull stop --pid-file /tmp/rapidcull-dev.pid
```

**Notes**

- If the PID file exists but the process is already gone, the command prints a warning about a stale PID file and removes it without error.
- If no PID file is found, the command exits with an error.

---

### `rapidcull restart`

Stop a running server (if any) and start it again with the supplied options. Accepts the same options as `start`. If the server is not running but a stale PID file exists, the stale file is removed before starting.

**Options**

| Option | Type | Default | Required | Description |
|---|---|---|---|---|
| `--host` | string | `127.0.0.1` | No | Host address to bind the server to |
| `--port` | integer | `8000` | No | Port to bind the server to |
| `--pid-file` | path | `~/.local/run/rapidcull/rapidcull.pid` | No | Path to the PID file |
| `--db` | path | None | No | Path to `rapidcull.db` |
| `--library-root` | path | None | No | Root directory for the photo library |

**Examples**

```sh
# Restart with the same defaults
rapidcull restart

# Restart on a different port
rapidcull restart --port 9000

# Restart pointing at a different database
rapidcull restart --db /data/rapidcull.db --library-root /mnt/photos
```

---

### `rapidcull process-new`

Discover supported media files in a source directory, plan ingest actions, extract metadata via ExifTool, and generate proxy files. Prints a one-line summary of processed, skipped, and failed counts when complete.

**Options**

| Option | Type | Default | Required | Description |
|---|---|---|---|---|
| `--source-dir` | path (existing directory) | — | Yes | Source directory to scan for new media |
| `--raw-pipeline` / `--no-raw-pipeline` | flag | `--raw-pipeline` (enabled) | No | Enable or disable the RAW processing pipeline for proxy generation |

**Examples**

```sh
# Ingest all new media from a card dump directory
rapidcull process-new --source-dir /mnt/card/DCIM

# Ingest without RAW pipeline (e.g. only JPEGs present)
rapidcull process-new --source-dir /mnt/card/DCIM --no-raw-pipeline

# Ingest from a specific shoot folder
rapidcull process-new --source-dir ~/Pictures/2026-06-shoot
```

**Notes**

- `--source-dir` must exist and must be a directory; the CLI validates this before running.
- Items already known to the library are skipped automatically (`force_reprocess` is not exposed as a flag).
- Output format: `Processed: N | Skipped: N | Failed: N`

---

### `rapidcull backup`

Back up the SQLite database and any gallery JSON state to a timestamped subdirectory under the specified backup root. Prints the number of files backed up, their total size in bytes, and the full path to the created backup directory.

**Options**

| Option | Type | Default | Required | Description |
|---|---|---|---|---|
| `--db` | path (existing file) | — | Yes | Path to `rapidcull.db` to back up |
| `--backup-root` | path | — | Yes | Parent directory under which the timestamped backup directory is created |
| `--galleries-root` | path (directory) | None | No | Path to the galleries root directory; gallery JSON files within it are included in the backup |

**Examples**

```sh
# Minimal backup (DB only)
rapidcull backup --db /data/rapidcull.db --backup-root /backups/rapidcull

# Backup DB and gallery state
rapidcull backup \
  --db /data/rapidcull.db \
  --galleries-root /data/galleries \
  --backup-root /backups/rapidcull

# Backup to a date-stamped external drive
rapidcull backup --db ~/rapidcull.db --backup-root /mnt/backup-drive/rapidcull
```

---

### `rapidcull restore`

Restore the SQLite database and gallery JSON state from a previously created backup directory. This is a destructive operation: existing files at the target paths are overwritten. The `--confirmed` flag is mandatory to prevent accidental data loss.

**Options**

| Option | Type | Default | Required | Description |
|---|---|---|---|---|
| `--backup-path` | path (existing directory) | — | Yes | Path to the backup directory created by `backup` |
| `--db` | path | — | Yes | Destination path to restore the database to |
| `--galleries-root` | path (directory) | None | No | Destination galleries root directory; gallery JSON files are restored here if present in the backup |
| `--confirmed` | flag | `false` | No* | Must be set to confirm that existing data will be overwritten |

*`--confirmed` is not technically marked `required=True` in the option definition, but the command exits with an error if it is not supplied.

**Examples**

```sh
# Restore a backup (--confirmed required)
rapidcull restore \
  --backup-path /backups/rapidcull/2026-06-19T120000 \
  --db /data/rapidcull.db \
  --confirmed

# Restore DB and galleries from a backup
rapidcull restore \
  --backup-path /backups/rapidcull/2026-06-19T120000 \
  --db /data/rapidcull.db \
  --galleries-root /data/galleries \
  --confirmed
```

**Notes**

- Omitting `--confirmed` prints `Error: --confirmed flag required to overwrite existing data` and exits with code 1.
- If the restore operation itself fails, the error reason is printed to stderr and the command exits with code 1.

---

### `rapidcull check`

Check consistency between the SQLite database and the filesystem. Reports all detected issues with their kind, item ID, and detail message. Optionally repairs detected drift when `--repair` is combined with `--confirmed`.

**Options**

| Option | Type | Default | Required | Description |
|---|---|---|---|---|
| `--db` | path (existing file) | — | Yes | Path to `rapidcull.db` to check |
| `--trash-dir` | path (directory) | None | No | Path to the trash directory; included in the consistency check when supplied |
| `--repair` | flag | `false` | No | Attempt to repair detected issues after reporting them |
| `--confirmed` | flag | `false` | No* | Must be set when `--repair` is used |

*`--confirmed` is required in practice whenever `--repair` is specified. Without it the command exits with an error.

**Examples**

```sh
# Check consistency and report issues (read-only)
rapidcull check --db /data/rapidcull.db

# Check including the trash directory
rapidcull check --db /data/rapidcull.db --trash-dir /data/trash

# Check and repair (--confirmed required)
rapidcull check --db /data/rapidcull.db --repair --confirmed

# Check, include trash, and repair
rapidcull check \
  --db /data/rapidcull.db \
  --trash-dir /data/trash \
  --repair \
  --confirmed
```

**Notes**

- Without `--repair`, the command is read-only and safe to run at any time.
- With `--repair` but without `--confirmed`, the command prints `Error: --confirmed required with --repair` and exits with code 1.
- Repair output: `Repaired: N fixed, N failed`
- Check output includes a timestamp (`Checked at:`), total issue count, and one line per issue in the format `[kind] item_id: detail`.
