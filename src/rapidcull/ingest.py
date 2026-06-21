from __future__ import annotations

from pathlib import Path
from typing import Protocol

from .exiftool_adapter import (
    ExifToolExtractionFailure,
    ExifToolExtractionOutcome,
    ExifToolExtractionSuccess,
)
from .models import FailedIngestItem, IngestMetadataExtractionResult, IngestPlan


class ExifMetadataExtractor(Protocol):
    def extract(self, path: Path) -> ExifToolExtractionOutcome: ...

    def restart(self) -> None: ...


def _pick_string_value(
    metadata: dict[str, str | int | float | bool | None],
    candidates: list[str],
) -> str | None:
    for key in candidates:
        value = metadata.get(key)
        if isinstance(value, str):
            return value
    return None


def normalize_exif_metadata(
    metadata: dict[str, str | int | float | bool | None],
) -> dict[str, str | int | float | bool | None]:
    result: dict[str, str | int | float | bool | None] = {}
    for key, value in metadata.items():
        base_key = key.split(":")[-1] if ":" in key else key
        if base_key not in result:
            result[base_key] = value

    result["file_type"] = _pick_string_value(
        metadata,
        ["File:FileType", "Unknown:FileType", "FileType"],
    )

    result["capture_datetime"] = _pick_string_value(
        metadata,
        [
            "EXIF:DateTimeOriginal",
            "Unknown:DateTimeOriginal",
            "DateTimeOriginal",
            "EXIF:CreateDate",
            "Unknown:CreateDate",
            "CreateDate",
            "Copy1:DateTimeOriginal",
            "Copy1:CreateDate",
        ],
    )

    result["camera_make"] = _pick_string_value(
        metadata,
        ["IFD0:Make", "EXIF:Make", "Unknown:Make", "Copy1:Make", "Make"],
    )

    result["camera_model"] = _pick_string_value(
        metadata,
        ["IFD0:Model", "EXIF:Model", "Unknown:Model", "Copy1:Model", "Model"],
    )

    return result


SUPPORTED_MEDIA_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".heic",
    ".mp4",
    ".mov",
    ".avi",
    ".mkv",
    ".webm",
    ".cr2",
    ".nef",
    ".arw",
    ".dng",
}


def discover_supported_media(roots: list[Path]) -> list[Path]:
    discovered: list[Path] = []

    for root in roots:
        for path in root.rglob("*"):
            if (
                path.is_file()
                and path.suffix.lower() in SUPPORTED_MEDIA_EXTENSIONS
                and not path.name.endswith(".proxy.jpg")
            ):
                discovered.append(path)

    return sorted(discovered)


def build_file_fingerprint(path: Path) -> str:
    stat = path.stat()
    return f"{path}:{stat.st_mtime_ns}:{stat.st_size}"


def load_known_fingerprints(db_path: Path) -> dict[Path, str]:
    """Load fingerprints for all known images by computing from current filesystem stat."""
    import sqlite3
    try:
        with sqlite3.connect(db_path) as conn:
            rows = conn.execute("SELECT path FROM images").fetchall()
    except sqlite3.OperationalError:
        return {}
    result: dict[Path, str] = {}
    for (path_str,) in rows:
        p = Path(path_str)
        try:
            result[p] = build_file_fingerprint(p)
        except OSError:
            pass
    return result


def plan_ingest_actions(
    discovered_files: list[Path],
    known_fingerprints: dict[Path, str],
    force_reprocess: bool,
) -> IngestPlan:
    if force_reprocess:
        return IngestPlan(to_process=sorted(discovered_files), skipped=[])

    to_process: list[Path] = []
    skipped: list[Path] = []

    for path in sorted(discovered_files):
        current_fingerprint = build_file_fingerprint(path)
        known_fingerprint = known_fingerprints.get(path)

        if known_fingerprint == current_fingerprint:
            skipped.append(path)
        else:
            to_process.append(path)

    return IngestPlan(to_process=to_process, skipped=skipped)


def extract_metadata_for_ingest(
    paths: list[Path],
    extractor: ExifMetadataExtractor,
) -> IngestMetadataExtractionResult:
    metadata_by_path: dict[Path, dict[str, str | int | float | bool | None]] = {}
    failed_items: list[FailedIngestItem] = []

    for path in sorted(paths):
        extraction_result = extractor.extract(path)
        if (
            isinstance(extraction_result, ExifToolExtractionFailure)
            and extraction_result.reason == "transport_error"
        ):
            try:
                extractor.restart()
            except Exception:
                # Restart itself failed — record item as failed and move on.
                # FR-002d: continue-on-error must hold even when restart crashes.
                failed_items.append(
                    FailedIngestItem(
                        path=str(path.resolve()),
                        reason="tool_error",
                    )
                )
                continue
            extraction_result = extractor.extract(path)

        if isinstance(extraction_result, ExifToolExtractionSuccess):
            metadata_by_path[path.resolve()] = normalize_exif_metadata(extraction_result.metadata)
            continue

        if isinstance(extraction_result, ExifToolExtractionFailure):
            failed_items.append(
                FailedIngestItem(
                    path=str(path.resolve()),
                    reason=(
                        "tool_error"
                        if extraction_result.reason == "transport_error"
                        else extraction_result.reason
                    ),
                )
            )

    return IngestMetadataExtractionResult(
        metadata_by_path=metadata_by_path,
        failed_items=failed_items,
    )
