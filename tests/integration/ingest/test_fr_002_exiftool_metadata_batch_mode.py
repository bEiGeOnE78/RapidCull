from __future__ import annotations

from pathlib import Path

import pytest

from rapidcull.exiftool_adapter import ExifToolBatchExtractor
from rapidcull.ingest import extract_metadata_for_ingest
from rapidcull.models import FailedIngestItem


@pytest.mark.fr
@pytest.mark.integration
def test_fr_002a_002c_extracts_metadata_for_multiple_assets_with_deterministic_mapping(
    tmp_path: Path,
) -> None:
    first = tmp_path / "first.jpg"
    second = tmp_path / "second.heic"
    first.write_text("a")
    second.write_text("b")

    extractor = ExifToolBatchExtractor()
    extractor.enqueue_success(
        path=first,
        metadata={
            "File:FileType": "JPEG",
            "EXIF:DateTimeOriginal": "2026:03:14 10:00:00",
            "IFD0:Make": "RapidCull",
            "IFD0:Model": "FixtureCamA",
        },
    )
    extractor.enqueue_success(
        path=second,
        metadata={
            "File:FileType": "HEIC",
            "EXIF:DateTimeOriginal": "2026:03:14 10:00:01",
            "IFD0:Make": "RapidCull",
            "IFD0:Model": "FixtureCamB",
        },
    )

    result = extract_metadata_for_ingest(paths=[second, first], extractor=extractor)

    assert list(result.metadata_by_path.keys()) == [first, second]
    assert result.metadata_by_path[first] == {
        "file_type": "JPEG",
        "capture_datetime": "2026:03:14 10:00:00",
        "camera_make": "RapidCull",
        "camera_model": "FixtureCamA",
    }
    assert result.metadata_by_path[second] == {
        "file_type": "HEIC",
        "capture_datetime": "2026:03:14 10:00:01",
        "camera_make": "RapidCull",
        "camera_model": "FixtureCamB",
    }
    assert result.failed_items == []


@pytest.mark.fr
@pytest.mark.integration
def test_fr_002d_continues_on_error_and_reports_per_item_failure_reasons(tmp_path: Path) -> None:
    first = tmp_path / "first.jpg"
    second = tmp_path / "second.jpg"
    first.write_text("a")
    second.write_text("b")

    extractor = ExifToolBatchExtractor()
    extractor.enqueue_success(
        path=first, metadata={"File:FileType": "JPEG", "IFD0:Model": "CamOne"}
    )
    extractor.enqueue_failure(path=second, reason="tool_error")

    result = extract_metadata_for_ingest(paths=[first, second], extractor=extractor)

    assert result.metadata_by_path == {
        first: {
            "file_type": "JPEG",
            "capture_datetime": None,
            "camera_make": None,
            "camera_model": "CamOne",
        }
    }
    assert result.failed_items == [
        FailedIngestItem(path=str(second.resolve()), reason="tool_error"),
    ]


@pytest.mark.fr
@pytest.mark.integration
def test_fr_002d_reports_malformed_batch_response_as_parse_error(tmp_path: Path) -> None:
    target = tmp_path / "target.jpg"
    target.write_text("a")

    extractor = ExifToolBatchExtractor()
    extractor.enqueue_malformed_response(path=target)

    result = extract_metadata_for_ingest(paths=[target], extractor=extractor)

    assert result.metadata_by_path == {}
    assert result.failed_items == [
        FailedIngestItem(path=str(target.resolve()), reason="parse_error"),
    ]


@pytest.mark.fr
@pytest.mark.integration
def test_fr_002d_restarts_after_transport_failure_and_recovers_next_request(tmp_path: Path) -> None:
    first = tmp_path / "first.jpg"
    second = tmp_path / "second.jpg"
    first.write_text("a")
    second.write_text("b")

    extractor = ExifToolBatchExtractor()
    extractor.enqueue_transport_failure(path=first)
    extractor.enqueue_success(
        path=first,
        metadata={"File:FileType": "JPEG", "IFD0:Model": "RecoveredCam"},
    )
    extractor.enqueue_success(
        path=second,
        metadata={"File:FileType": "JPEG", "IFD0:Model": "StableCam"},
    )

    result = extract_metadata_for_ingest(paths=[first, second], extractor=extractor)

    assert result.failed_items == []
    assert result.metadata_by_path[first] == {
        "file_type": "JPEG",
        "capture_datetime": None,
        "camera_make": None,
        "camera_model": "RecoveredCam",
    }
    assert result.metadata_by_path[second] == {
        "file_type": "JPEG",
        "capture_datetime": None,
        "camera_make": None,
        "camera_model": "StableCam",
    }


@pytest.mark.fr
@pytest.mark.integration
def test_fr_002d_records_failure_when_retry_exhausted_after_transport_failure(
    tmp_path: Path,
) -> None:
    target = tmp_path / "target.jpg"
    target.write_text("a")

    extractor = ExifToolBatchExtractor()
    extractor.enqueue_transport_failure(path=target)
    extractor.enqueue_transport_failure(path=target)

    result = extract_metadata_for_ingest(paths=[target], extractor=extractor)

    assert result.metadata_by_path == {}
    assert result.failed_items == [
        FailedIngestItem(path=str(target.resolve()), reason="tool_error"),
    ]
