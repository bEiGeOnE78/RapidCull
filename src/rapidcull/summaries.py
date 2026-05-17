from __future__ import annotations

from .models import FailedIngestItem, IngestRunSummary


def build_ingest_run_summary(
    processed_count: int,
    skipped_count: int,
    failed_items: list[FailedIngestItem],
) -> IngestRunSummary:
    return IngestRunSummary(
        processed_count=processed_count,
        skipped_count=skipped_count,
        failed_count=len(failed_items),
        failed_items=failed_items,
    )
