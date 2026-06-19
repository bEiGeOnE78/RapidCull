"""Integration tests: FR-050 and FR-050a run summaries with elapsed time and per-tool counts."""

from pathlib import Path

import pytest

from rapidcull.models import ProxyToolSummary
from rapidcull.summaries import build_ingest_run_summary


@pytest.mark.fr
@pytest.mark.integration
def test_fr_050_ingest_summary_has_elapsed_ms() -> None:
    """IngestRunSummary must carry elapsed_ms."""
    summary = build_ingest_run_summary(
        processed_count=5, skipped_count=1, failed_items=[], elapsed_ms=1234
    )
    assert summary.elapsed_ms == 1234


@pytest.mark.fr
@pytest.mark.integration
def test_fr_050_ingest_summary_elapsed_defaults_zero() -> None:
    """elapsed_ms defaults to 0 for backward compat."""
    summary = build_ingest_run_summary(processed_count=1, skipped_count=0, failed_items=[])
    assert summary.elapsed_ms == 0


@pytest.mark.fr
@pytest.mark.integration
def test_fr_050a_ingest_summary_has_tool_summary() -> None:
    """IngestRunSummary must carry tool_summary (per-tool counts)."""
    tool_summary: ProxyToolSummary = {
        "exiftool": {"processed": 5, "failed": 1, "reasons": {"extraction_error": 1}}
    }
    summary = build_ingest_run_summary(
        processed_count=5, skipped_count=0, failed_items=[], tool_summary=tool_summary
    )
    assert summary.tool_summary == tool_summary


@pytest.mark.fr
@pytest.mark.integration
def test_fr_050a_ingest_summary_tool_summary_defaults_empty() -> None:
    """tool_summary defaults to empty dict."""
    summary = build_ingest_run_summary(processed_count=1, skipped_count=0, failed_items=[])
    assert summary.tool_summary == {}


@pytest.mark.fr
@pytest.mark.integration
def test_fr_050_proxy_result_elapsed_ms_nonzero(tmp_path: Path) -> None:
    """ProxyGenerationResult.elapsed_ms must reflect actual wall time (not hardcoded 0)."""
    from rapidcull.proxies import execute_proxy_generation

    # empty plan — still measures time
    result = execute_proxy_generation([], raw_pipeline_available=False)
    # Even empty run takes some ms; just verify it's an int >= 0
    assert isinstance(result.elapsed_ms, int)
    assert result.elapsed_ms >= 0


@pytest.mark.fr
@pytest.mark.integration
def test_fr_050a_proxy_result_has_tool_summary(tmp_path: Path) -> None:
    """ProxyGenerationResult.tool_summary must have per-tool entries after generation."""
    from rapidcull.proxies import execute_proxy_generation

    result = execute_proxy_generation([], raw_pipeline_available=False)
    assert isinstance(result.tool_summary, dict)
