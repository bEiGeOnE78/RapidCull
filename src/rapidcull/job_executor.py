"""Background job executor for RapidCull (FR-042).

Single-threaded pool (max_workers=1) for SQLite safety.
"""

from __future__ import annotations

import dataclasses
import sqlite3
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from rapidcull.backup import backup
from rapidcull.consistency import check_consistency, repair_consistency
from rapidcull.culling import hard_delete, list_decisions, list_trash, move_to_trash
from rapidcull.faces import cluster_faces, detect_and_store_faces
from rapidcull.galleries import create_gallery_from_mode, rebuild_galleries_index
from rapidcull.identity import create_image_record, get_paths_with_missing_proxies, update_display_path, update_full_path, update_metadata, update_thumbnail_path
from rapidcull.ingest import (
    discover_supported_media,
    extract_metadata_for_ingest,
    load_known_fingerprints,
    plan_ingest_actions,
)
from rapidcull.jobs import JobStore
from rapidcull.models import ClusterMode
from rapidcull.proxies import execute_proxy_generation

ProgressLog = Callable[[str], None]


class JobExecutor:
    """Dispatches jobs to underlying RapidCull functions in a single background thread."""

    def __init__(self, db_path: Path, library_root: Path | None = None) -> None:
        self._db_path = db_path
        self._library_root = library_root
        self._proxy_dir = db_path.parent / "proxies"
        self._gallery_dir = db_path.parent / "galleries"
        self._trash_dir = db_path.parent / ".trash"
        self._backup_dir = db_path.parent / "backups"
        self._pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="job-executor")

    def submit(self, job_id: str, kind: str, store: JobStore) -> None:
        self._pool.submit(self._run, job_id, kind, store)

    def _run(self, job_id: str, kind: str, store: JobStore) -> None:
        store.mark_running(job_id)

        def log(msg: str) -> None:
            store.append_progress(job_id, msg)

        try:
            result = self._dispatch(kind, log)
            store.mark_succeeded(job_id, result)
        except Exception as exc:
            store.mark_failed(job_id, str(exc))

    def _dispatch(self, kind: str, log: ProgressLog) -> dict[str, Any]:
        match kind:
            case "ingest_and_proxy":
                return self._ingest_and_proxy(log)
            case "detect_faces":
                return self._detect_faces(log)
            case "cluster_faces":
                return self._cluster_faces(log)
            case "create_gallery_picks":
                return self._create_gallery_picks(log)
            case "move_rejects_to_trash":
                return self._move_rejects_to_trash(log)
            case "hard_delete_trash":
                return self._hard_delete_trash(log)
            case "rebuild_galleries_index":
                return self._rebuild_galleries_index(log)
            case "backup":
                return self._backup(log)
            case "check_consistency":
                return self._check_consistency(log)
            case "repair_consistency":
                return self._repair_consistency(log)
            case _:
                raise ValueError(f"Unknown job kind: {kind!r}")

    def _ingest_and_proxy(self, log: ProgressLog) -> dict[str, Any]:
        if self._library_root is None:
            raise RuntimeError("library_root not configured; cannot run ingest_and_proxy")
        from rapidcull.exiftool_adapter import RealExifToolBatchExtractor  # noqa: PLC0415

        log(f"Discovering media in {self._library_root} ...")
        discovered = discover_supported_media([self._library_root])
        log(f"Found {len(discovered)} files")
        known_fps = load_known_fingerprints(self._db_path) if self._db_path.exists() else {}
        plan = plan_ingest_actions(discovered, known_fps, force_reprocess=False)
        log(f"To process: {len(plan.to_process)}, skipped: {len(plan.skipped)}")
        processed = 0
        failed_items = []
        if plan.to_process:
            log("Extracting metadata ...")
            with RealExifToolBatchExtractor() as extractor:
                extraction = extract_metadata_for_ingest(plan.to_process, extractor)
            for path in extraction.metadata_by_path:
                create_image_record(self._db_path, path)
                processed += 1
            for path, meta in extraction.metadata_by_path.items():
                update_metadata(self._db_path, path, meta)
            failed_items.extend(extraction.failed_items)
            log(f"Stored {processed} image records")
            log("Generating proxies ...")
            proxy_result = execute_proxy_generation(
                plan.to_process,
                raw_pipeline_available=True,
                proxy_dir=self._proxy_dir,
                library_root=self._library_root if self._library_root is not None else self._proxy_dir,
            )
            failed_items.extend(proxy_result.failed)
            for gp in proxy_result.generated:
                if gp.thumbnail_path:
                    update_thumbnail_path(self._db_path, Path(gp.source_path), Path(gp.thumbnail_path))
                if gp.display_path:
                    update_display_path(self._db_path, Path(gp.source_path), Path(gp.display_path))
                if gp.full_path:
                    update_full_path(self._db_path, Path(gp.source_path), Path(gp.full_path))
            log(f"Proxies: {proxy_result.processed_count} generated")
        # Fill proxies for already-ingested files with null proxy paths
        filled_count = 0
        if self._db_path is not None and self._db_path.exists():
            missing_proxy_paths = get_paths_with_missing_proxies(self._db_path)
            if missing_proxy_paths:
                log(f"Filling proxies for {len(missing_proxy_paths)} files with missing proxy paths ...")
                fill_result = execute_proxy_generation(
                    missing_proxy_paths,
                    raw_pipeline_available=True,
                    proxy_dir=self._proxy_dir,
                    library_root=self._library_root if self._library_root is not None else self._proxy_dir,
                )
                failed_items.extend(fill_result.failed)
                for gp in fill_result.generated:
                    if gp.thumbnail_path:
                        update_thumbnail_path(self._db_path, Path(gp.source_path), Path(gp.thumbnail_path))
                    if gp.display_path:
                        update_display_path(self._db_path, Path(gp.source_path), Path(gp.display_path))
                    if gp.full_path:
                        update_full_path(self._db_path, Path(gp.source_path), Path(gp.full_path))
                filled_count = fill_result.processed_count
                log(f"Fill pass: {filled_count} proxies generated")
        log(
            f"Ingest complete: {processed} processed, "
            f"{len(plan.skipped)} skipped, {len(failed_items)} failed"
        )
        return {
            "processed_count": processed,
            "skipped_count": len(plan.skipped),
            "failed_count": len(failed_items),
            "filled_proxy_count": filled_count,
        }

    def _detect_faces(self, log: ProgressLog) -> dict[str, Any]:
        from rapidcull.adapters.insightface_adapter import InsightFaceAdapter  # noqa: PLC0415

        log("Loading image list from DB ...")
        with sqlite3.connect(self._db_path) as conn:
            rows = conn.execute("SELECT path FROM images").fetchall()
        image_paths = [Path(r[0]) for r in rows]
        log(f"Detecting faces in {len(image_paths)} images ...")
        detector = InsightFaceAdapter()
        result = detect_and_store_faces(self._db_path, image_paths, detector)
        log(f"Done: {result.processed_count} processed, {result.failed_count} failed")
        return dataclasses.asdict(result)

    def _cluster_faces(self, log: ProgressLog) -> dict[str, Any]:
        log("Clustering faces ...")
        result = cluster_faces(self._db_path, mode=ClusterMode.ALL)
        log(
            f"Done: {result.person_count} persons, "
            f"{result.assigned_count} assigned, {result.noise_count} noise"
        )
        return dataclasses.asdict(result)

    def _create_gallery_picks(self, log: ProgressLog) -> dict[str, Any]:
        log("Loading pick decisions ...")
        decisions = list_decisions(self._db_path, filter="pick")
        log(f"Found {len(decisions)} picks")
        pick_paths: list[Path] = []
        with sqlite3.connect(self._db_path) as conn:
            for d in decisions:
                row = conn.execute(
                    "SELECT path FROM images WHERE image_id = ?", (d.image_id,)
                ).fetchone()
                if row:
                    pick_paths.append(Path(row[0]))
        gallery_dir = self._gallery_dir / "picks"
        log(f"Creating gallery at {gallery_dir} with {len(pick_paths)} assets ...")
        result = create_gallery_from_mode(gallery_dir, "picks", {"picks": pick_paths})
        log(f"Done: {len(result.created_paths)} hardlinks created")
        return {
            "gallery_path": result.gallery_path,
            "created_count": len(result.created_paths),
            "skipped_count": len(result.skipped_paths),
        }

    def _move_rejects_to_trash(self, log: ProgressLog) -> dict[str, Any]:
        log("Loading reject decisions ...")
        decisions = list_decisions(self._db_path, filter="reject")
        image_ids = [d.image_id for d in decisions]
        log(f"Moving {len(image_ids)} rejects to trash ...")
        result = move_to_trash(self._db_path, image_ids, self._trash_dir)
        log(f"Done: {result.moved_count} moved, {result.failed_count} failed")
        return dataclasses.asdict(result)

    def _hard_delete_trash(self, log: ProgressLog) -> dict[str, Any]:
        log("Loading trash contents ...")
        items = list_trash(self._db_path)
        image_ids = [i.image_id for i in items]
        log(f"Hard deleting {len(image_ids)} items ...")
        result = hard_delete(self._db_path, image_ids, self._trash_dir, confirmed=True)
        log(f"Done: {result.deleted_count} deleted, {result.failed_count} failed")
        return {"deleted_count": result.deleted_count, "failed_count": result.failed_count}

    def _rebuild_galleries_index(self, log: ProgressLog) -> dict[str, Any]:
        self._gallery_dir.mkdir(parents=True, exist_ok=True)
        log(f"Rebuilding galleries index at {self._gallery_dir} ...")
        result = rebuild_galleries_index(self._gallery_dir)
        log(f"Done: {result.gallery_count} galleries indexed")
        return {
            "index_path": result.index_path,
            "gallery_count": result.gallery_count,
            "processed_count": result.processed_count,
            "failed_count": result.failed_count,
        }

    def _backup(self, log: ProgressLog) -> dict[str, Any]:
        self._backup_dir.mkdir(parents=True, exist_ok=True)
        log(f"Backing up to {self._backup_dir} ...")
        result = backup(self._db_path, self._gallery_dir, self._backup_dir)
        log(f"Done: {result.files_backed_up} files, {result.total_bytes} bytes")
        return dataclasses.asdict(result)

    def _check_consistency(self, log: ProgressLog) -> dict[str, Any]:
        log("Checking consistency ...")
        result = check_consistency(self._db_path, self._trash_dir)
        log(f"Done: {len(result.issues)} issues found")
        return {
            "issues": [dataclasses.asdict(i) for i in result.issues],
            "checked_at": result.checked_at,
        }

    def _repair_consistency(self, log: ProgressLog) -> dict[str, Any]:
        log("Checking consistency ...")
        report = check_consistency(self._db_path, self._trash_dir)
        log(f"Found {len(report.issues)} issues, repairing ...")
        result = repair_consistency(self._db_path, report, self._trash_dir, confirmed=True)
        log(
            f"Done: {result.fixed_count} fixed, "
            f"{result.skipped_count} skipped, {result.failed_count} failed"
        )
        return dataclasses.asdict(result)
