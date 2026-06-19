from __future__ import annotations

import time
from pathlib import Path

from .adapters import ImageMagickAdapter, RawTherapeeAdapter
from .models import (
    FailedIngestItem,
    GeneratedProxy,
    OrphanCleanupReport,
    ProxyGenerationPlan,
    ProxyGenerationResult,
    ProxyToolSummary,
    RegenerationSelectionResult,
)


def build_proxy_generation_plan(paths: list[Path]) -> ProxyGenerationPlan:
    still_image_suffixes = {".jpg", ".jpeg", ".png", ".heic", ".cr2", ".nef", ".arw", ".dng"}
    heic_suffixes = {".heic"}
    raw_suffixes = {".cr2", ".nef", ".arw", ".dng"}

    thumbnail_targets: list[Path] = []
    heic_display_proxy_targets: list[Path] = []
    raw_proxy_targets: list[Path] = []

    for path in sorted(paths):
        suffix = path.suffix.lower()

        if suffix in still_image_suffixes:
            thumbnail_targets.append(path)

        if suffix in heic_suffixes:
            heic_display_proxy_targets.append(path)

        if suffix in raw_suffixes:
            raw_proxy_targets.append(path)

    return ProxyGenerationPlan(
        thumbnail_targets=thumbnail_targets,
        heic_display_proxy_targets=heic_display_proxy_targets,
        raw_proxy_targets=raw_proxy_targets,
    )


def execute_proxy_generation(
    paths: list[Path],
    raw_pipeline_available: bool,
    imagemagick_adapter: ImageMagickAdapter | None = None,
    rawtherapee_adapter: RawTherapeeAdapter | None = None,
) -> ProxyGenerationResult:
    start = time.perf_counter()
    imagemagick = imagemagick_adapter or ImageMagickAdapter()
    rawtherapee = rawtherapee_adapter or RawTherapeeAdapter()

    still_suffixes = {".jpg", ".jpeg", ".png"}
    heic_suffixes = {".heic"}
    raw_suffixes = {".cr2", ".nef", ".arw", ".dng"}
    video_suffixes = {".mp4", ".mov", ".avi", ".mkv", ".webm"}
    generated: list[GeneratedProxy] = []
    failed: list[FailedIngestItem] = []
    tool_summary: ProxyToolSummary = {
        "imagemagick": _initial_tool_stats(),
        "rawtherapee": _initial_tool_stats(),
        "orchestrator": _initial_tool_stats(),
    }

    for path in sorted(paths):
        suffix = path.suffix.lower()
        resolved_path = str(path.resolve())

        if suffix in video_suffixes:
            generated.append(GeneratedProxy(source_path=resolved_path, proxy_kind="video_mp4_h264"))
            continue

        if suffix in still_suffixes:
            increment_tool_counter(tool_summary, tool="imagemagick", counter="processed")
            still_outcome = imagemagick.generate_still_thumbnail(path)
            if still_outcome.ok:
                generated.append(
                    GeneratedProxy(source_path=resolved_path, proxy_kind="thumbnail_still")
                )
                increment_tool_counter(tool_summary, tool="imagemagick", counter="generated")
            else:
                reason = "imagemagick_still_failed"
                failed.append(
                    FailedIngestItem(
                        path=resolved_path,
                        reason=reason,
                    )
                )
                record_failure(tool_summary, tool="imagemagick", reason=reason)
            continue

        if suffix in heic_suffixes:
            increment_tool_counter(tool_summary, tool="imagemagick", counter="processed")
            heic_outcome = imagemagick.generate_heic_proxy(path)
            if heic_outcome.ok:
                generated.append(
                    GeneratedProxy(source_path=resolved_path, proxy_kind="heic_display_proxy")
                )
                increment_tool_counter(tool_summary, tool="imagemagick", counter="generated")
            else:
                reason = normalize_imagemagick_heic_reason(heic_outcome.reason)
                failed.append(
                    FailedIngestItem(
                        path=resolved_path,
                        reason=reason,
                    )
                )
                record_failure(tool_summary, tool="imagemagick", reason=reason)
            continue

        if suffix not in raw_suffixes:
            increment_tool_counter(tool_summary, tool="orchestrator", counter="processed")
            reason = "unsupported_media_type"
            failed.append(FailedIngestItem(path=resolved_path, reason=reason))
            record_failure(tool_summary, tool="orchestrator", reason=reason)
            continue

        increment_tool_counter(tool_summary, tool="rawtherapee", counter="processed")
        raw_outcome = rawtherapee.generate_raw_proxy(
            path=path, pipeline_available=raw_pipeline_available
        )
        if raw_outcome.ok:
            generated.append(GeneratedProxy(source_path=resolved_path, proxy_kind="raw_jpg"))
            increment_tool_counter(tool_summary, tool="rawtherapee", counter="generated")
        else:
            reason = normalize_rawtherapee_reason(raw_outcome.reason)
            failed.append(
                FailedIngestItem(
                    path=resolved_path,
                    reason=reason,
                )
            )
            record_failure(tool_summary, tool="rawtherapee", reason=reason)

    return ProxyGenerationResult(
        generated=generated,
        failed=failed,
        processed_count=len(paths),
        skipped_count=0,
        failed_count=len(failed),
        elapsed_ms=int((time.perf_counter() - start) * 1000),
        tool_summary=tool_summary,
    )


def _initial_tool_stats() -> dict[str, int | dict[str, int]]:
    return {"processed": 0, "generated": 0, "failed": 0, "reasons": {}}


def increment_tool_counter(
    tool_summary: ProxyToolSummary,
    tool: str,
    counter: str,
) -> None:
    current_stats = tool_summary[tool]
    current_value = current_stats[counter]
    assert isinstance(current_value, int)
    current_stats[counter] = current_value + 1


def record_failure(
    tool_summary: ProxyToolSummary,
    tool: str,
    reason: str,
) -> None:
    increment_tool_counter(tool_summary, tool=tool, counter="failed")
    reasons = tool_summary[tool]["reasons"]
    assert isinstance(reasons, dict)
    current_count = reasons.get(reason, 0)
    reasons[reason] = current_count + 1


def normalize_rawtherapee_reason(reason: str | None) -> str:
    if reason == "rawtherapee_pipeline_unavailable":
        return reason
    return "rawtherapee_failed"


def normalize_imagemagick_heic_reason(reason: str | None) -> str:
    if reason == "imagemagick_heif_unsupported":
        return reason
    return "imagemagick_heic_failed"


def execute_regeneration_selection(
    available_assets_by_id: dict[str, str],
    selected_ids: list[str] | None,
) -> RegenerationSelectionResult:
    if selected_ids is None:
        return RegenerationSelectionResult(
            selected_paths=sorted(available_assets_by_id.values()),
            invalid_ids=[],
            mode="bulk",
        )

    selected_paths: list[str] = []
    invalid_ids: list[str] = []

    for image_id in selected_ids:
        path = available_assets_by_id.get(image_id)
        if path is None:
            invalid_ids.append(image_id)
            continue
        selected_paths.append(path)

    return RegenerationSelectionResult(
        selected_paths=selected_paths,
        invalid_ids=invalid_ids,
        mode="selected",
    )


def cleanup_orphan_artifacts(
    artifact_paths: list[Path],
    active_artifact_paths: set[Path],
) -> OrphanCleanupReport:
    deleted_paths: list[str] = []

    for artifact_path in sorted(artifact_paths):
        if artifact_path in active_artifact_paths:
            continue

        if artifact_path.exists():
            artifact_path.unlink()
        deleted_paths.append(str(artifact_path.resolve()))

    return OrphanCleanupReport(deleted_count=len(deleted_paths), deleted_paths=deleted_paths)
