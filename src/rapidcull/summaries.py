from __future__ import annotations

from .models import FailedIngestItem, IngestRunSummary, ProxyToolSummary


def build_ingest_run_summary(
    processed_count: int,
    skipped_count: int,
    failed_items: list[FailedIngestItem],
    elapsed_ms: int = 0,
    tool_summary: ProxyToolSummary | None = None,
) -> IngestRunSummary:
    return IngestRunSummary(
        processed_count=processed_count,
        skipped_count=skipped_count,
        failed_count=len(failed_items),
        failed_items=failed_items,
        elapsed_ms=elapsed_ms,
        tool_summary=tool_summary if tool_summary is not None else {},
    )
