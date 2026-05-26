from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from rapidcull.cli import cli
from rapidcull.models import (
    FailedIngestItem,
    IngestMetadataExtractionResult,
    IngestPlan,
    ProxyGenerationResult,
)


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


def _make_extraction_result(
    paths: list[Path],
    failed: list[FailedIngestItem] | None = None,
) -> IngestMetadataExtractionResult:
    """Build an IngestMetadataExtractionResult with one metadata entry per path."""
    metadata: dict[Path, dict[str, str | int | float | bool | None]] = {
        p: {
            "file_type": "JPEG",
            "capture_datetime": None,
            "camera_make": None,
            "camera_model": None,
        }
        for p in paths
    }
    return IngestMetadataExtractionResult(
        metadata_by_path=metadata,
        failed_items=failed or [],
    )


def _make_proxy_result(
    failed: list[FailedIngestItem] | None = None,
) -> ProxyGenerationResult:
    """Build a ProxyGenerationResult with optional failures."""
    return ProxyGenerationResult(
        generated=[],
        failed=failed or [],
        processed_count=0,
        skipped_count=0,
        failed_count=len(failed) if failed else 0,
        elapsed_ms=0,
    )


class TestProcessNewMissingSourceDir:
    def test_nonexistent_directory_errors(self, runner: CliRunner, tmp_path: Path) -> None:
        """process-new errors when --source-dir does not exist."""
        nonexistent = tmp_path / "no_such_dir"

        result = runner.invoke(cli, ["process-new", "--source-dir", str(nonexistent)])

        # Click's exists=True check produces a non-zero exit before our code runs,
        # but also guard against our own sys.exit path.
        assert result.exit_code != 0

    def test_nonexistent_directory_output_contains_error(
        self, runner: CliRunner, tmp_path: Path
    ) -> None:
        """process-new prints a useful error message for missing source directories."""
        nonexistent = tmp_path / "no_such_dir"

        result = runner.invoke(cli, ["process-new", "--source-dir", str(nonexistent)])

        combined = (result.output + (result.stderr or "")).lower()
        # Click's error message says "does not exist"; accept that or our own message
        assert "does not exist" in combined or "invalid value" in combined or "error" in combined


class TestProcessNewEmptyDir:
    def test_empty_dir_reports_zero_counts(self, runner: CliRunner, tmp_path: Path) -> None:
        """process-new with an empty source directory reports Processed: 0."""
        source_dir = tmp_path / "empty_source"
        source_dir.mkdir()

        with patch("rapidcull.cli.discover_supported_media", return_value=[]):
            result = runner.invoke(cli, ["process-new", "--source-dir", str(source_dir)])

        assert result.exit_code == 0
        assert "Processed: 0" in result.output
        assert "Skipped: 0" in result.output
        assert "Failed: 0" in result.output

    def test_empty_dir_does_not_call_plan_or_extract(
        self, runner: CliRunner, tmp_path: Path
    ) -> None:
        """process-new short-circuits without calling downstream pipeline when nothing is found."""
        source_dir = tmp_path / "empty_source"
        source_dir.mkdir()

        with (
            patch("rapidcull.cli.discover_supported_media", return_value=[]),
            patch("rapidcull.cli.plan_ingest_actions") as mock_plan,
            patch("rapidcull.cli.extract_metadata_for_ingest") as mock_extract,
        ):
            runner.invoke(cli, ["process-new", "--source-dir", str(source_dir)])

        mock_plan.assert_not_called()
        mock_extract.assert_not_called()


class TestProcessNewHappyPath:
    def test_happy_path_reports_correct_counts(self, runner: CliRunner, tmp_path: Path) -> None:
        """Report correct counts for 3 files with 1 skipped."""
        source_dir = tmp_path / "source"
        source_dir.mkdir()

        paths = [
            source_dir / "a.jpg",
            source_dir / "b.jpg",
            source_dir / "c.jpg",
        ]
        skipped = [source_dir / "d.jpg"]
        plan = IngestPlan(to_process=paths, skipped=skipped)
        extraction_result = _make_extraction_result(paths)
        proxy_result = _make_proxy_result()

        mock_extractor = MagicMock()

        with (
            patch("rapidcull.cli.discover_supported_media", return_value=paths + skipped),
            patch("rapidcull.cli.plan_ingest_actions", return_value=plan),
            patch(
                "rapidcull.cli.RealExifToolBatchExtractor",
                return_value=mock_extractor,
            ),
            patch("rapidcull.cli.extract_metadata_for_ingest", return_value=extraction_result),
            patch("rapidcull.cli.execute_proxy_generation", return_value=proxy_result),
        ):
            # Make the context manager work on our mock extractor
            mock_extractor.__enter__ = MagicMock(return_value=mock_extractor)
            mock_extractor.__exit__ = MagicMock(return_value=False)

            result = runner.invoke(cli, ["process-new", "--source-dir", str(source_dir)])

        assert result.exit_code == 0
        assert "Processed: 3" in result.output
        assert "Skipped: 1" in result.output
        assert "Failed: 0" in result.output

    def test_happy_path_output_format(self, runner: CliRunner, tmp_path: Path) -> None:
        """process-new output follows 'Processed: N | Skipped: N | Failed: N' format."""
        source_dir = tmp_path / "source"
        source_dir.mkdir()

        paths = [source_dir / "img.jpg"]
        plan = IngestPlan(to_process=paths, skipped=[])
        extraction_result = _make_extraction_result(paths)
        proxy_result = _make_proxy_result()
        mock_extractor = MagicMock()

        with (
            patch("rapidcull.cli.discover_supported_media", return_value=paths),
            patch("rapidcull.cli.plan_ingest_actions", return_value=plan),
            patch("rapidcull.cli.RealExifToolBatchExtractor", return_value=mock_extractor),
            patch("rapidcull.cli.extract_metadata_for_ingest", return_value=extraction_result),
            patch("rapidcull.cli.execute_proxy_generation", return_value=proxy_result),
        ):
            mock_extractor.__enter__ = MagicMock(return_value=mock_extractor)
            mock_extractor.__exit__ = MagicMock(return_value=False)

            result = runner.invoke(cli, ["process-new", "--source-dir", str(source_dir)])

        assert result.exit_code == 0
        # Full canonical format check
        assert "Processed: 1 | Skipped: 0 | Failed: 0" in result.output


class TestProcessNewWithFailures:
    def test_extraction_and_proxy_failures_accumulate(
        self, runner: CliRunner, tmp_path: Path
    ) -> None:
        """process-new sums failures from both extraction and proxy generation stages."""
        source_dir = tmp_path / "source"
        source_dir.mkdir()

        paths = [
            source_dir / "a.jpg",
            source_dir / "b.jpg",
            source_dir / "c.jpg",
        ]
        plan = IngestPlan(to_process=paths, skipped=[])

        # 1 failure at extraction stage
        extraction_failed = [FailedIngestItem(path=str(paths[0]), reason="tool_error")]
        # extraction only has metadata for the 2 that succeeded
        extraction_result = IngestMetadataExtractionResult(
            metadata_by_path={
                p: {
                    "file_type": "JPEG",
                    "capture_datetime": None,
                    "camera_make": None,
                    "camera_model": None,
                }
                for p in paths[1:]
            },
            failed_items=extraction_failed,
        )

        # 1 failure at proxy generation stage
        proxy_failed = [FailedIngestItem(path=str(paths[1]), reason="convert_error")]
        proxy_result = _make_proxy_result(failed=proxy_failed)

        mock_extractor = MagicMock()

        with (
            patch("rapidcull.cli.discover_supported_media", return_value=paths),
            patch("rapidcull.cli.plan_ingest_actions", return_value=plan),
            patch("rapidcull.cli.RealExifToolBatchExtractor", return_value=mock_extractor),
            patch("rapidcull.cli.extract_metadata_for_ingest", return_value=extraction_result),
            patch("rapidcull.cli.execute_proxy_generation", return_value=proxy_result),
        ):
            mock_extractor.__enter__ = MagicMock(return_value=mock_extractor)
            mock_extractor.__exit__ = MagicMock(return_value=False)

            result = runner.invoke(cli, ["process-new", "--source-dir", str(source_dir)])

        assert result.exit_code == 0
        assert "Failed: 2" in result.output

    def test_only_extraction_failures(self, runner: CliRunner, tmp_path: Path) -> None:
        """process-new reports only extraction failures when proxy generation succeeds."""
        source_dir = tmp_path / "source"
        source_dir.mkdir()

        paths = [source_dir / "x.jpg", source_dir / "y.jpg"]
        plan = IngestPlan(to_process=paths, skipped=[])

        failed_item = FailedIngestItem(path=str(paths[0]), reason="unsupported_format")
        extraction_result = IngestMetadataExtractionResult(
            metadata_by_path={
                paths[1]: {
                    "file_type": "JPEG",
                    "capture_datetime": None,
                    "camera_make": None,
                    "camera_model": None,
                }
            },
            failed_items=[failed_item],
        )
        proxy_result = _make_proxy_result()
        mock_extractor = MagicMock()

        with (
            patch("rapidcull.cli.discover_supported_media", return_value=paths),
            patch("rapidcull.cli.plan_ingest_actions", return_value=plan),
            patch("rapidcull.cli.RealExifToolBatchExtractor", return_value=mock_extractor),
            patch("rapidcull.cli.extract_metadata_for_ingest", return_value=extraction_result),
            patch("rapidcull.cli.execute_proxy_generation", return_value=proxy_result),
        ):
            mock_extractor.__enter__ = MagicMock(return_value=mock_extractor)
            mock_extractor.__exit__ = MagicMock(return_value=False)

            result = runner.invoke(cli, ["process-new", "--source-dir", str(source_dir)])

        assert result.exit_code == 0
        assert "Failed: 1" in result.output
        assert "Processed: 1" in result.output

    def test_only_proxy_failures(self, runner: CliRunner, tmp_path: Path) -> None:
        """process-new reports only proxy failures when metadata extraction fully succeeds."""
        source_dir = tmp_path / "source"
        source_dir.mkdir()

        paths = [source_dir / "a.cr2", source_dir / "b.cr2"]
        plan = IngestPlan(to_process=paths, skipped=[])
        extraction_result = _make_extraction_result(paths)

        proxy_failed = [FailedIngestItem(path=str(p), reason="rawtherapee_error") for p in paths]
        proxy_result = _make_proxy_result(failed=proxy_failed)
        mock_extractor = MagicMock()

        with (
            patch("rapidcull.cli.discover_supported_media", return_value=paths),
            patch("rapidcull.cli.plan_ingest_actions", return_value=plan),
            patch("rapidcull.cli.RealExifToolBatchExtractor", return_value=mock_extractor),
            patch("rapidcull.cli.extract_metadata_for_ingest", return_value=extraction_result),
            patch("rapidcull.cli.execute_proxy_generation", return_value=proxy_result),
        ):
            mock_extractor.__enter__ = MagicMock(return_value=mock_extractor)
            mock_extractor.__exit__ = MagicMock(return_value=False)

            result = runner.invoke(cli, ["process-new", "--source-dir", str(source_dir)])

        assert result.exit_code == 0
        assert "Failed: 2" in result.output
        assert "Processed: 2" in result.output


class TestProcessNewSkippedItems:
    def test_skipped_items_do_not_pass_through_pipeline(
        self, runner: CliRunner, tmp_path: Path
    ) -> None:
        """process-new does not call extract or proxy stages for skipped files."""
        source_dir = tmp_path / "source"
        source_dir.mkdir()

        all_paths = [source_dir / "new.jpg", source_dir / "known.jpg"]
        plan = IngestPlan(to_process=[], skipped=all_paths)

        with (
            patch("rapidcull.cli.discover_supported_media", return_value=all_paths),
            patch("rapidcull.cli.plan_ingest_actions", return_value=plan),
            patch("rapidcull.cli.extract_metadata_for_ingest") as mock_extract,
            patch("rapidcull.cli.execute_proxy_generation") as mock_proxy,
        ):
            result = runner.invoke(cli, ["process-new", "--source-dir", str(source_dir)])

        assert result.exit_code == 0
        assert "Skipped: 2" in result.output
        assert "Processed: 0" in result.output
        mock_extract.assert_not_called()
        mock_proxy.assert_not_called()
