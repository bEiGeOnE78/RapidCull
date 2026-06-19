from __future__ import annotations

import os
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path

import click

from rapidcull.backup import backup as run_backup
from rapidcull.backup import restore as run_restore
from rapidcull.consistency import check_consistency, repair_consistency
from rapidcull.exiftool_adapter import RealExifToolBatchExtractor
from rapidcull.ingest import (
    discover_supported_media,
    extract_metadata_for_ingest,
    plan_ingest_actions,
)
from rapidcull.models import FailedIngestItem
from rapidcull.path_utils import normalize_path
from rapidcull.proxies import execute_proxy_generation
from rapidcull.summaries import build_ingest_run_summary

_DEFAULT_PID_FILE = Path.home() / ".local" / "run" / "rapidcull" / "rapidcull.pid"
_DEFAULT_HOST = "127.0.0.1"
_DEFAULT_PORT = 8000


def _read_pid(pid_file: Path) -> int | None:
    """Read PID from file. Return None if missing or invalid."""
    if not pid_file.exists():
        return None
    try:
        return int(pid_file.read_text().strip())
    except (ValueError, OSError):
        return None


def _process_alive(pid: int) -> bool:
    """Check if process with given PID is alive."""
    try:
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, PermissionError):
        return False


def _port_in_use(host: str, port: int) -> bool:
    """Check if port is already in use."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        result = sock.connect_ex((host, port))
        return result == 0
    finally:
        sock.close()


@click.group()
def cli() -> None:
    """RapidCull — local photo library toolkit."""


@cli.command()
@click.option("--host", default=_DEFAULT_HOST, help="Host to bind to")
@click.option("--port", default=_DEFAULT_PORT, type=int, help="Port to bind to")
@click.option(
    "--pid-file", type=click.Path(), default=str(_DEFAULT_PID_FILE), help="Path to PID file"
)
def start(host: str, port: int, pid_file: str) -> None:
    """Start the RapidCull API server."""
    pid_path = Path(pid_file)

    # Check if already running
    existing_pid = _read_pid(pid_path)
    if existing_pid is not None and _process_alive(existing_pid):
        click.echo(f"Error: RapidCull already running (PID={existing_pid})", err=True)
        sys.exit(1)

    # Check if port is in use
    if _port_in_use(host, port):
        click.echo(f"Error: port {port} already in use", err=True)
        sys.exit(1)

    # Create PID file directory
    pid_path.parent.mkdir(parents=True, exist_ok=True)

    # Start the server
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "rapidcull.api:app", "--host", host, "--port", str(port)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
        env=os.environ.copy(),
    )

    # Write PID file
    pid_path.write_text(f"{proc.pid}\n")

    click.echo(f"RapidCull API started on http://{host}:{port} (PID={proc.pid})")


@cli.command()
@click.option(
    "--pid-file", type=click.Path(), default=str(_DEFAULT_PID_FILE), help="Path to PID file"
)
def stop(pid_file: str) -> None:
    """Stop the RapidCull API server."""
    pid_path = Path(pid_file)

    # Read PID
    pid = _read_pid(pid_path)
    if pid is None:
        click.echo("Error: no running service found", err=True)
        sys.exit(1)

    # Check if process is alive
    if not _process_alive(pid):
        click.echo(f"Warning: stale PID file (PID={pid}), removing", err=True)
        pid_path.unlink(missing_ok=True)
        return

    # Send SIGTERM
    os.kill(pid, signal.SIGTERM)

    # Wait for graceful shutdown (50 iterations × 0.1s = 5 seconds)
    for _ in range(50):
        if not _process_alive(pid):
            break
        time.sleep(0.1)

    # If still alive, send SIGKILL
    if _process_alive(pid):
        os.kill(pid, signal.SIGKILL)

    # Remove PID file
    pid_path.unlink(missing_ok=True)

    click.echo(f"RapidCull API stopped (PID={pid})")


@cli.command()
@click.option("--host", default=_DEFAULT_HOST, help="Host to bind to")
@click.option("--port", default=_DEFAULT_PORT, type=int, help="Port to bind to")
@click.option(
    "--pid-file", type=click.Path(), default=str(_DEFAULT_PID_FILE), help="Path to PID file"
)
@click.pass_context
def restart(ctx: click.Context, host: str, port: int, pid_file: str) -> None:
    """Restart the RapidCull API server."""
    pid_path = Path(pid_file)

    # Stop if running
    existing_pid = _read_pid(pid_path)
    if existing_pid is not None and _process_alive(existing_pid):
        ctx.invoke(stop, pid_file=pid_file)
    elif pid_path.exists():
        pid_path.unlink(missing_ok=True)

    # Start
    ctx.invoke(start, host=host, port=port, pid_file=pid_file)


@cli.command(name="process-new")
@click.option(
    "--source-dir",
    required=True,
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="Source directory to ingest",
)
@click.option(
    "--raw-pipeline/--no-raw-pipeline", default=True, help="Enable RAW processing pipeline"
)
def process_new(source_dir: str, raw_pipeline: bool) -> None:
    """Process new media from source directory."""
    source_path = normalize_path(source_dir)

    # Discover supported media
    discovered = discover_supported_media([source_path])

    if not discovered:
        click.echo("Processed: 0 | Skipped: 0 | Failed: 0")
        return

    # Plan ingest actions
    plan = plan_ingest_actions(discovered, {}, force_reprocess=False)

    # Collect all failed items
    all_failed: list[FailedIngestItem] = []
    processed_count = 0

    if plan.to_process:
        # Extract metadata using context manager
        with RealExifToolBatchExtractor() as extractor:
            extraction_result = extract_metadata_for_ingest(plan.to_process, extractor)
            all_failed.extend(extraction_result.failed_items)
            processed_count = len(extraction_result.metadata_by_path)

        # Generate proxies
        proxy_result = execute_proxy_generation(
            plan.to_process, raw_pipeline_available=raw_pipeline
        )
        all_failed.extend(proxy_result.failed)

    # Build summary
    summary = build_ingest_run_summary(
        processed_count=processed_count,
        skipped_count=len(plan.skipped),
        failed_items=all_failed,
    )

    processed = summary.processed_count
    skipped = summary.skipped_count
    failed = summary.failed_count
    click.echo(f"Processed: {processed} | Skipped: {skipped} | Failed: {failed}")


@cli.command(name="backup")
@click.option(
    "--db",
    required=True,
    type=click.Path(exists=True, dir_okay=False),
    help="Path to rapidcull.db",
)
@click.option(
    "--galleries-root",
    type=click.Path(file_okay=False),
    default=None,
    help="Path to galleries root directory",
)
@click.option(
    "--backup-root",
    required=True,
    type=click.Path(),
    help="Directory to store backups",
)
def backup_cmd(db: str, galleries_root: str | None, backup_root: str) -> None:
    """Backup DB and gallery JSON state to a timestamped directory."""
    result = run_backup(
        db_path=Path(db),
        galleries_root=Path(galleries_root) if galleries_root else None,
        backup_root=Path(backup_root),
    )
    click.echo(
        f"Backed up {result.files_backed_up} file(s) ({result.total_bytes} bytes)"
        f" -> {result.backup_path}"
    )


@cli.command(name="restore")
@click.option(
    "--backup-path",
    required=True,
    type=click.Path(exists=True, file_okay=False),
    help="Path to backup directory",
)
@click.option(
    "--db",
    required=True,
    type=click.Path(dir_okay=False),
    help="Path to restore DB to",
)
@click.option(
    "--galleries-root",
    type=click.Path(file_okay=False),
    default=None,
    help="Path to galleries root directory",
)
@click.option(
    "--confirmed",
    is_flag=True,
    default=False,
    help="Required to confirm restore (overwrites existing data)",
)
def restore_cmd(backup_path: str, db: str, galleries_root: str | None, confirmed: bool) -> None:
    """Restore DB and gallery JSON from a backup directory."""
    if not confirmed:
        click.echo("Error: --confirmed flag required to overwrite existing data", err=True)
        raise SystemExit(1)
    result = run_restore(
        backup_path=Path(backup_path),
        db_path=Path(db),
        galleries_root=Path(galleries_root) if galleries_root else None,
        confirmed=confirmed,
    )
    if result.success:
        click.echo(f"Restored {result.files_restored} file(s) from {backup_path}")
    else:
        click.echo(f"Error: {result.reason}", err=True)
        raise SystemExit(1)


@cli.command(name="check")
@click.option(
    "--db",
    required=True,
    type=click.Path(exists=True, dir_okay=False),
    help="Path to rapidcull.db",
)
@click.option(
    "--trash-dir",
    type=click.Path(file_okay=False),
    default=None,
    help="Path to trash directory",
)
@click.option("--repair", is_flag=True, default=False, help="Repair detected issues")
@click.option(
    "--confirmed",
    is_flag=True,
    default=False,
    help="Required when --repair is set",
)
def check_cmd(db: str, trash_dir: str | None, repair: bool, confirmed: bool) -> None:
    """Check DB/FS consistency and optionally repair drift."""
    report = check_consistency(
        db_path=Path(db),
        trash_dir=Path(trash_dir) if trash_dir else None,
    )
    click.echo(f"Checked at: {report.checked_at}")
    click.echo(f"Issues found: {len(report.issues)}")
    for issue in report.issues:
        click.echo(f"  [{issue.kind}] {issue.item_id}: {issue.detail}")

    if repair:
        if not confirmed:
            click.echo("Error: --confirmed required with --repair", err=True)
            raise SystemExit(1)
        result = repair_consistency(
            db_path=Path(db),
            report=report,
            trash_dir=Path(trash_dir) if trash_dir else None,
            confirmed=confirmed,
        )
        click.echo(f"Repaired: {result.fixed_count} fixed, {result.failed_count} failed")


def main() -> None:
    """Main entry point for RapidCull CLI."""
    cli()
