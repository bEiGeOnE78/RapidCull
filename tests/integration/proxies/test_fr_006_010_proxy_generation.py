from __future__ import annotations

from pathlib import Path

import pytest

from rapidcull.adapters import ImageMagickAdapter, RawTherapeeAdapter, RawTherapeeProxyOutcome
from rapidcull.adapters.imagemagick import ImageMagickProxyOutcome, detect_heif_support
from rapidcull.models import (
    FailedIngestItem,
    GeneratedProxy,
    OrphanCleanupReport,
    ProxyGenerationResult,
    RegenerationSelectionResult,
)
from rapidcull.proxies import (
    build_proxy_generation_plan,
    cleanup_orphan_artifacts,
    execute_proxy_generation,
    execute_regeneration_selection,
)


@pytest.mark.fr
@pytest.mark.integration
def test_fr_006_builds_thumbnails_for_supported_still_images(tmp_path: Path) -> None:
    still_image = tmp_path / "still.jpg"
    still_image.write_text("pixel-data")

    plan = build_proxy_generation_plan([still_image])

    assert plan.thumbnail_targets == [still_image]


@pytest.mark.fr
@pytest.mark.integration
def test_fr_007_plans_heic_display_proxies_for_heic_inputs(tmp_path: Path) -> None:
    heic_image = tmp_path / "portrait.heic"
    heic_image.write_text("heic-data")

    plan = build_proxy_generation_plan([heic_image])

    assert plan.heic_display_proxy_targets == [heic_image]


@pytest.mark.fr
@pytest.mark.integration
def test_fr_008_generates_raw_jpg_proxy_or_actionable_error(tmp_path: Path) -> None:
    raw_image = tmp_path / "capture.nef"
    raw_image.write_text("raw-data")

    class SuccessfulRawAdapter(RawTherapeeAdapter):
        def generate_raw_proxy(
            self,
            path: Path,
            pipeline_available: bool,
        ) -> RawTherapeeProxyOutcome:
            _ = path
            _ = pipeline_available
            return RawTherapeeProxyOutcome(ok=True, reason=None)

    failed_result = execute_proxy_generation(
        [raw_image],
        raw_pipeline_available=False,
    )

    assert failed_result == ProxyGenerationResult(
        generated=[],
        failed=[
            FailedIngestItem(
                path=str(raw_image.resolve()),
                reason="rawtherapee_pipeline_unavailable",
            )
        ],
        processed_count=1,
        skipped_count=0,
        failed_count=1,
        elapsed_ms=0,
        tool_summary={
            "imagemagick": {
                "processed": 0,
                "generated": 0,
                "failed": 0,
                "reasons": {},
            },
            "rawtherapee": {
                "processed": 1,
                "generated": 0,
                "failed": 1,
                "reasons": {"rawtherapee_pipeline_unavailable": 1},
            },
            "orchestrator": {
                "processed": 0,
                "generated": 0,
                "failed": 0,
                "reasons": {},
            },
        },
    )

    successful_result = execute_proxy_generation(
        [raw_image],
        raw_pipeline_available=True,
        rawtherapee_adapter=SuccessfulRawAdapter(),
    )

    assert successful_result == ProxyGenerationResult(
        generated=[
            GeneratedProxy(
                source_path=str(raw_image.resolve()),
                proxy_kind="raw_jpg",
            )
        ],
        failed=[],
        processed_count=1,
        skipped_count=0,
        failed_count=0,
        elapsed_ms=0,
        tool_summary={
            "imagemagick": {
                "processed": 0,
                "generated": 0,
                "failed": 0,
                "reasons": {},
            },
            "rawtherapee": {
                "processed": 1,
                "generated": 1,
                "failed": 0,
                "reasons": {},
            },
            "orchestrator": {
                "processed": 0,
                "generated": 0,
                "failed": 0,
                "reasons": {},
            },
        },
    )


@pytest.mark.fr
@pytest.mark.integration
def test_fr_006a_generates_still_thumbnail_proxy_via_proxy_execution(tmp_path: Path) -> None:
    class SuccessfulStillAdapter(ImageMagickAdapter):
        def generate_still_thumbnail(self, path: Path) -> ImageMagickProxyOutcome:
            _ = path
            return ImageMagickProxyOutcome(ok=True, reason=None)

    still_image = tmp_path / "still.jpg"
    still_image.write_text("pixel-data")

    result = execute_proxy_generation(
        [still_image],
        raw_pipeline_available=True,
        imagemagick_adapter=SuccessfulStillAdapter(heif_supported=True),
    )

    assert result == ProxyGenerationResult(
        generated=[
            GeneratedProxy(
                source_path=str(still_image.resolve()),
                proxy_kind="thumbnail_still",
            )
        ],
        failed=[],
        processed_count=1,
        skipped_count=0,
        failed_count=0,
        elapsed_ms=0,
        tool_summary={
            "imagemagick": {
                "processed": 1,
                "generated": 1,
                "failed": 0,
                "reasons": {},
            },
            "rawtherapee": {
                "processed": 0,
                "generated": 0,
                "failed": 0,
                "reasons": {},
            },
            "orchestrator": {
                "processed": 0,
                "generated": 0,
                "failed": 0,
                "reasons": {},
            },
        },
    )


@pytest.mark.fr
@pytest.mark.integration
def test_fr_007a_records_heic_tooling_failure_with_actionable_reason(tmp_path: Path) -> None:
    heic_image = tmp_path / "portrait.heic"
    heic_image.write_text("heic-data")

    result = execute_proxy_generation(
        [heic_image],
        raw_pipeline_available=True,
        imagemagick_adapter=ImageMagickAdapter(heif_supported=False),
    )

    assert result.failed == [
        FailedIngestItem(
            path=str(heic_image.resolve()),
            reason="imagemagick_heif_unsupported",
        )
    ]


@pytest.mark.fr
@pytest.mark.integration
def test_fr_008b_proxy_run_accounting_is_deterministic_per_item(tmp_path: Path) -> None:
    still = tmp_path / "still.jpg"
    heic = tmp_path / "portrait.heic"
    raw = tmp_path / "capture.nef"
    for path in [still, heic, raw]:
        path.write_text("data")

    result = execute_proxy_generation(
        [still, raw, heic],
        raw_pipeline_available=False,
    )

    accounted_paths = {proxy.source_path for proxy in result.generated} | {
        failure.path for failure in result.failed
    }
    expected_paths = {str(still.resolve()), str(heic.resolve()), str(raw.resolve())}

    assert accounted_paths == expected_paths


@pytest.mark.fr
@pytest.mark.integration
def test_fr_008b_batch_proxy_orchestration_accounts_each_input_exactly_once(
    tmp_path: Path,
) -> None:
    class SuccessfulStillAdapter(ImageMagickAdapter):
        def generate_still_thumbnail(self, path: Path) -> ImageMagickProxyOutcome:
            _ = path
            return ImageMagickProxyOutcome(ok=True, reason=None)

    still = tmp_path / "still.jpg"
    heic = tmp_path / "portrait.heic"
    raw = tmp_path / "capture.nef"
    unsupported = tmp_path / "notes.txt"
    for path in [still, heic, raw, unsupported]:
        path.write_text("data")

    result = execute_proxy_generation(
        [unsupported, still, heic, raw],
        raw_pipeline_available=False,
        imagemagick_adapter=SuccessfulStillAdapter(heif_supported=False),
    )

    assert result.failed == [
        FailedIngestItem(
            path=str(raw.resolve()),
            reason="rawtherapee_pipeline_unavailable",
        ),
        FailedIngestItem(
            path=str(unsupported.resolve()),
            reason="unsupported_media_type",
        ),
        FailedIngestItem(
            path=str(heic.resolve()),
            reason="imagemagick_heif_unsupported",
        ),
    ]


@pytest.mark.fr
@pytest.mark.integration
def test_fr_007a_generates_heic_proxy_when_heif_capability_is_available(tmp_path: Path) -> None:
    class SuccessfulHeicAdapter(ImageMagickAdapter):
        def generate_heic_proxy(self, path: Path) -> ImageMagickProxyOutcome:
            _ = path
            return ImageMagickProxyOutcome(ok=True, reason=None)

    heic_image = tmp_path / "supported.heic"
    heic_image.write_text("heic-data")

    result = execute_proxy_generation(
        [heic_image],
        raw_pipeline_available=True,
        imagemagick_adapter=SuccessfulHeicAdapter(heif_supported=True),
    )

    assert result == ProxyGenerationResult(
        generated=[
            GeneratedProxy(
                source_path=str(heic_image.resolve()),
                proxy_kind="heic_display_proxy",
            )
        ],
        failed=[],
        processed_count=1,
        skipped_count=0,
        failed_count=0,
        elapsed_ms=0,
        tool_summary={
            "imagemagick": {
                "processed": 1,
                "generated": 1,
                "failed": 0,
                "reasons": {},
            },
            "rawtherapee": {
                "processed": 0,
                "generated": 0,
                "failed": 0,
                "reasons": {},
            },
            "orchestrator": {
                "processed": 0,
                "generated": 0,
                "failed": 0,
                "reasons": {},
            },
        },
    )


@pytest.mark.fr
@pytest.mark.integration
@pytest.mark.skipif(
    not detect_heif_support(),
    reason="HEIF support not available in current environment (ImageMagick not built with HEIF)",
)
def test_fr_007a_detect_heif_support_is_true_in_current_environment() -> None:
    assert detect_heif_support() is True


@pytest.mark.fr
@pytest.mark.integration
def test_fr_008b_returns_generated_and_failed_lists_sorted_by_path(tmp_path: Path) -> None:
    class SuccessfulStillAdapter(ImageMagickAdapter):
        def generate_still_thumbnail(self, path: Path) -> ImageMagickProxyOutcome:
            _ = path
            return ImageMagickProxyOutcome(ok=True, reason=None)

    still_b = tmp_path / "b-still.jpg"
    heic_a = tmp_path / "a-heic.heic"
    raw_c = tmp_path / "c-raw.nef"

    for path in [still_b, heic_a, raw_c]:
        path.write_text("data")

    result = execute_proxy_generation(
        [raw_c, still_b, heic_a],
        raw_pipeline_available=False,
        imagemagick_adapter=SuccessfulStillAdapter(heif_supported=False),
    )

    assert [proxy.source_path for proxy in result.generated] == [str(still_b.resolve())]
    assert [failure.path for failure in result.failed] == [
        str(heic_a.resolve()),
        str(raw_c.resolve()),
    ]


@pytest.mark.fr
@pytest.mark.integration
def test_fr_050a_proxy_result_exposes_deterministic_per_tool_summary(tmp_path: Path) -> None:
    class SuccessfulStillAdapter(ImageMagickAdapter):
        def generate_still_thumbnail(self, path: Path) -> ImageMagickProxyOutcome:
            _ = path
            return ImageMagickProxyOutcome(ok=True, reason=None)

    still = tmp_path / "still.jpg"
    heic = tmp_path / "capture.heic"
    raw = tmp_path / "capture.nef"
    unsupported = tmp_path / "notes.txt"

    for path in [still, heic, raw, unsupported]:
        path.write_text("data")

    result = execute_proxy_generation(
        [unsupported, raw, heic, still],
        raw_pipeline_available=False,
        imagemagick_adapter=SuccessfulStillAdapter(heif_supported=False),
    )

    assert result.tool_summary == {
        "imagemagick": {
            "processed": 2,
            "generated": 1,
            "failed": 1,
            "reasons": {"imagemagick_heif_unsupported": 1},
        },
        "rawtherapee": {
            "processed": 1,
            "generated": 0,
            "failed": 1,
            "reasons": {"rawtherapee_pipeline_unavailable": 1},
        },
        "orchestrator": {
            "processed": 1,
            "generated": 0,
            "failed": 1,
            "reasons": {"unsupported_media_type": 1},
        },
    }


@pytest.mark.fr
@pytest.mark.integration
def test_fr_050_proxy_result_exposes_run_summary_counts(tmp_path: Path) -> None:
    class SuccessfulStillAdapter(ImageMagickAdapter):
        def generate_still_thumbnail(self, path: Path) -> ImageMagickProxyOutcome:
            _ = path
            return ImageMagickProxyOutcome(ok=True, reason=None)

    still = tmp_path / "still.jpg"
    heic = tmp_path / "capture.heic"
    raw = tmp_path / "capture.nef"
    unsupported = tmp_path / "notes.txt"

    for path in [still, heic, raw, unsupported]:
        path.write_text("data")

    result = execute_proxy_generation(
        [unsupported, raw, heic, still],
        raw_pipeline_available=False,
        imagemagick_adapter=SuccessfulStillAdapter(heif_supported=False),
    )

    assert result.processed_count == 4
    assert result.skipped_count == 0
    assert result.failed_count == 3
    assert result.elapsed_ms >= 0


@pytest.mark.fr
@pytest.mark.integration
def test_fr_006a_normalizes_imagemagick_still_failure_reason(tmp_path: Path) -> None:
    class FailingStillAdapter(ImageMagickAdapter):
        def generate_still_thumbnail(self, path: Path) -> ImageMagickProxyOutcome:
            _ = path
            return ImageMagickProxyOutcome(ok=False, reason="thumbnail command failed")

    still = tmp_path / "still.jpg"
    still.write_text("data")

    result = execute_proxy_generation(
        [still],
        raw_pipeline_available=True,
        imagemagick_adapter=FailingStillAdapter(heif_supported=True),
    )

    assert result.failed == [
        FailedIngestItem(
            path=str(still.resolve()),
            reason="imagemagick_still_failed",
        )
    ]
    assert result.tool_summary["imagemagick"]["reasons"] == {
        "imagemagick_still_failed": 1,
    }


@pytest.mark.fr
@pytest.mark.integration
def test_fr_007a_normalizes_heic_subprocess_detail_to_canonical_reason(
    tmp_path: Path,
) -> None:
    class HeicExitDetailAdapter(ImageMagickAdapter):
        def generate_heic_proxy(self, path: Path) -> ImageMagickProxyOutcome:
            _ = path
            return ImageMagickProxyOutcome(ok=False, reason="imagemagick_exit_1")

    heic = tmp_path / "capture.heic"
    heic.write_text("heic-data")

    result = execute_proxy_generation(
        [heic],
        raw_pipeline_available=True,
        imagemagick_adapter=HeicExitDetailAdapter(heif_supported=True),
    )

    assert result.failed == [
        FailedIngestItem(
            path=str(heic.resolve()),
            reason="imagemagick_heic_failed",
        )
    ]
    assert result.tool_summary["imagemagick"]["reasons"] == {
        "imagemagick_heic_failed": 1,
    }


@pytest.mark.fr
@pytest.mark.integration
def test_fr_008a_normalizes_rawtherapee_subprocess_detail_to_canonical_reason(
    tmp_path: Path,
) -> None:
    class RawExitDetailAdapter(RawTherapeeAdapter):
        def generate_raw_proxy(
            self,
            path: Path,
            pipeline_available: bool,
        ) -> RawTherapeeProxyOutcome:
            _ = path
            _ = pipeline_available
            return RawTherapeeProxyOutcome(ok=False, reason="rawtherapee_exit_1")

    raw = tmp_path / "capture.nef"
    raw.write_text("raw-data")

    result = execute_proxy_generation(
        [raw],
        raw_pipeline_available=True,
        rawtherapee_adapter=RawExitDetailAdapter(),
    )

    assert result.failed == [
        FailedIngestItem(
            path=str(raw.resolve()),
            reason="rawtherapee_failed",
        )
    ]
    assert result.tool_summary["rawtherapee"]["reasons"] == {
        "rawtherapee_failed": 1,
    }


@pytest.mark.fr
@pytest.mark.integration
def test_fr_008a_uses_subprocess_capable_rawtherapee_adapter_contract(tmp_path: Path) -> None:
    class SubprocessStyleRawAdapter(RawTherapeeAdapter):
        def __init__(self) -> None:
            self.invocations: list[tuple[Path, bool]] = []

        def generate_raw_proxy(
            self,
            path: Path,
            pipeline_available: bool,
        ) -> RawTherapeeProxyOutcome:
            self.invocations.append((path.resolve(), pipeline_available))
            if pipeline_available:
                return RawTherapeeProxyOutcome(ok=True, reason=None)
            return RawTherapeeProxyOutcome(ok=False, reason="rawtherapee_pipeline_unavailable")

    raw = tmp_path / "capture.nef"
    raw.write_text("raw-data")

    adapter = SubprocessStyleRawAdapter()
    result = execute_proxy_generation(
        [raw],
        raw_pipeline_available=True,
        rawtherapee_adapter=adapter,
    )

    assert adapter.invocations == [(raw.resolve(), True)]
    assert result.generated == [
        GeneratedProxy(source_path=str(raw.resolve()), proxy_kind="raw_jpg"),
    ]


@pytest.mark.fr
@pytest.mark.integration
def test_fr_008a_rawtherapee_adapter_invokes_subprocess_when_pipeline_available(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    raw = tmp_path / "capture.nef"
    raw.write_text("raw-data")

    recorded_commands: list[list[str]] = []

    def fake_run_command(self: RawTherapeeAdapter, command: list[str]) -> int:
        _ = self
        recorded_commands.append(command)
        return 0

    monkeypatch.setattr(RawTherapeeAdapter, "_run_command", fake_run_command)

    adapter = RawTherapeeAdapter()
    outcome = adapter.generate_raw_proxy(path=raw, pipeline_available=True)

    expected_output = raw.with_name(raw.stem + ".proxy.jpg")
    assert recorded_commands == [
        [
            "rawtherapee-cli",
            "-o",
            str(expected_output.resolve()),
            str(raw.resolve()),
        ]
    ]
    assert outcome == RawTherapeeProxyOutcome(ok=True, reason=None)


@pytest.mark.fr
@pytest.mark.integration
def test_fr_008a_rawtherapee_adapter_maps_nonzero_exit_to_canonical_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    raw = tmp_path / "capture.nef"
    raw.write_text("raw-data")

    def fake_run_command(self: RawTherapeeAdapter, command: list[str]) -> int:
        _ = (self, command)
        return 3

    monkeypatch.setattr(RawTherapeeAdapter, "_run_command", fake_run_command)

    adapter = RawTherapeeAdapter()
    outcome = adapter.generate_raw_proxy(path=raw, pipeline_available=True)

    assert outcome == RawTherapeeProxyOutcome(ok=False, reason="rawtherapee_failed")


@pytest.mark.fr
@pytest.mark.integration
def test_fr_006a_imagemagick_adapter_invokes_subprocess_for_still_thumbnail(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    still = tmp_path / "still.jpg"
    still.write_text("pixel-data")

    recorded_commands: list[list[str]] = []

    def fake_run_command(self: ImageMagickAdapter, command: list[str]) -> int:
        _ = self
        recorded_commands.append(command)
        return 0

    monkeypatch.setattr(ImageMagickAdapter, "_run_command", fake_run_command)

    adapter = ImageMagickAdapter(heif_supported=True)
    outcome = adapter.generate_still_thumbnail(path=still)

    expected_output = still.with_name(still.stem + ".proxy.jpg")
    assert recorded_commands == [
        [
            "magick",
            str(still.resolve()),
            str(expected_output.resolve()),
        ]
    ]
    assert outcome == ImageMagickProxyOutcome(ok=True, reason=None)


@pytest.mark.fr
@pytest.mark.integration
def test_fr_007a_imagemagick_adapter_invokes_subprocess_for_heic_proxy(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    heic = tmp_path / "capture.heic"
    heic.write_text("heic-data")

    recorded_commands: list[list[str]] = []

    def fake_run_command(self: ImageMagickAdapter, command: list[str]) -> int:
        _ = self
        recorded_commands.append(command)
        return 0

    monkeypatch.setattr(ImageMagickAdapter, "_run_command", fake_run_command)

    adapter = ImageMagickAdapter(heif_supported=True)
    outcome = adapter.generate_heic_proxy(path=heic)

    expected_output = heic.with_name(heic.stem + ".proxy.jpg")
    assert recorded_commands == [
        [
            "magick",
            str(heic.resolve()),
            str(expected_output.resolve()),
        ]
    ]
    assert outcome == ImageMagickProxyOutcome(ok=True, reason=None)


@pytest.mark.fr
@pytest.mark.integration
def test_fr_007a_imagemagick_adapter_maps_heic_nonzero_exit_to_canonical_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    heic = tmp_path / "capture.heic"
    heic.write_text("heic-data")

    def fake_run_command(self: ImageMagickAdapter, command: list[str]) -> int:
        _ = (self, command)
        return 2

    monkeypatch.setattr(ImageMagickAdapter, "_run_command", fake_run_command)

    adapter = ImageMagickAdapter(heif_supported=True)
    outcome = adapter.generate_heic_proxy(path=heic)

    assert outcome == ImageMagickProxyOutcome(ok=False, reason="imagemagick_heic_nonzero_exit")


@pytest.mark.fr
@pytest.mark.integration
def test_fr_007a_imagemagick_adapter_maps_heic_oserror_to_canonical_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    heic = tmp_path / "capture.heic"
    heic.write_text("heic-data")

    def fake_run_command(self: ImageMagickAdapter, command: list[str]) -> int:
        _ = (self, command)
        raise OSError("magick missing")

    monkeypatch.setattr(ImageMagickAdapter, "_run_command", fake_run_command)

    adapter = ImageMagickAdapter(heif_supported=True)
    outcome = adapter.generate_heic_proxy(path=heic)

    assert outcome == ImageMagickProxyOutcome(ok=False, reason="imagemagick_heic_execution_error")


@pytest.mark.fr
@pytest.mark.integration
def test_fr_007a_imagemagick_adapter_maps_heic_timeout_to_detail_reason(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    heic = tmp_path / "capture.heic"
    heic.write_text("heic-data")

    def fake_run_command(self: ImageMagickAdapter, command: list[str]) -> int:
        _ = (self, command)
        raise TimeoutError("timed out")

    monkeypatch.setattr(ImageMagickAdapter, "_run_command", fake_run_command)

    adapter = ImageMagickAdapter(heif_supported=True)
    outcome = adapter.generate_heic_proxy(path=heic)

    assert outcome == ImageMagickProxyOutcome(ok=False, reason="imagemagick_heic_timeout")


@pytest.mark.fr
@pytest.mark.integration
def test_fr_009_generates_video_proxy_for_supported_video_inputs(tmp_path: Path) -> None:
    video = tmp_path / "clip.mov"
    video.write_text("video-data")

    result = execute_proxy_generation(
        [video],
        raw_pipeline_available=True,
    )

    assert result == ProxyGenerationResult(
        generated=[
            GeneratedProxy(
                source_path=str(video.resolve()),
                proxy_kind="video_mp4_h264",
            )
        ],
        failed=[],
        processed_count=1,
        skipped_count=0,
        failed_count=0,
        elapsed_ms=0,
        tool_summary={
            "imagemagick": {
                "processed": 0,
                "generated": 0,
                "failed": 0,
                "reasons": {},
            },
            "rawtherapee": {
                "processed": 0,
                "generated": 0,
                "failed": 0,
                "reasons": {},
            },
            "orchestrator": {
                "processed": 0,
                "generated": 0,
                "failed": 0,
                "reasons": {},
            },
        },
    )


@pytest.mark.fr
@pytest.mark.integration
def test_fr_010_supports_selected_and_bulk_regeneration_with_invalid_id_reporting() -> None:
    available = {
        "img_001": "/library/a.jpg",
        "img_002": "/library/b.heic",
        "img_003": "/library/c.mov",
    }

    selected_result = execute_regeneration_selection(
        available_assets_by_id=available,
        selected_ids=["img_001", "img_404", "img_003"],
    )

    assert selected_result == RegenerationSelectionResult(
        selected_paths=["/library/a.jpg", "/library/c.mov"],
        invalid_ids=["img_404"],
        mode="selected",
    )

    bulk_result = execute_regeneration_selection(
        available_assets_by_id=available,
        selected_ids=None,
    )

    assert bulk_result == RegenerationSelectionResult(
        selected_paths=["/library/a.jpg", "/library/b.heic", "/library/c.mov"],
        invalid_ids=[],
        mode="bulk",
    )


@pytest.mark.fr
@pytest.mark.integration
def test_fr_011_cleans_orphan_artifacts_and_returns_deletion_report(tmp_path: Path) -> None:
    artifact_root = tmp_path / "artifacts"
    artifact_root.mkdir()

    keep = artifact_root / "keep-thumb.jpg"
    stale_one = artifact_root / "stale-proxy-1.jpg"
    stale_two = artifact_root / "stale-proxy-2.mp4"

    for artifact in [keep, stale_one, stale_two]:
        artifact.write_text("artifact")

    report = cleanup_orphan_artifacts(
        artifact_paths=[keep, stale_one, stale_two],
        active_artifact_paths={keep},
    )

    assert report == OrphanCleanupReport(
        deleted_count=2,
        deleted_paths=[str(stale_one.resolve()), str(stale_two.resolve())],
    )
    assert keep.exists()
    assert not stale_one.exists()
    assert not stale_two.exists()
