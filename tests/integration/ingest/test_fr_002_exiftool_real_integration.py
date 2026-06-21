from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from rapidcull.exiftool_adapter import RealExifToolBatchExtractor
from rapidcull.ingest import extract_metadata_for_ingest


def _write_tiny_jpeg(path: Path) -> None:
    image_magick_binary = shutil.which("magick")
    if image_magick_binary is not None:
        command = [image_magick_binary, "-size", "1x1", "xc:white", str(path)]
    else:
        convert_binary = shutil.which("convert")
        if convert_binary is None:
            pytest.fail("Missing required system dependency: ImageMagick (magick/convert)")
        command = [convert_binary, "-size", "1x1", "xc:white", str(path)]

    subprocess.run(command, check=True, capture_output=True, text=True)


def _write_exif(path: Path, create_date: str, make: str, model: str) -> None:
    subprocess.run(
        [
            "exiftool",
            "-overwrite_original",
            f"-DateTimeOriginal={create_date}",
            f"-Make={make}",
            f"-Model={model}",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )


@pytest.mark.fr
@pytest.mark.integration
def test_fr_002b_002c_real_exiftool_batch_mode_extracts_known_metadata(tmp_path: Path) -> None:
    if shutil.which("exiftool") is None:
        pytest.fail("Missing required system dependency: exiftool")

    target = tmp_path / "fixture.jpg"
    _write_tiny_jpeg(target)
    _write_exif(
        path=target,
        create_date="2026:03:14 12:34:56",
        make="RapidCull",
        model="FixtureCam",
    )

    with RealExifToolBatchExtractor() as extractor:
        result = extract_metadata_for_ingest(paths=[target], extractor=extractor)

    assert result.failed_items == []
    metadata = result.metadata_by_path[target.resolve()]

    expected = {
        "file_type": "JPEG",
        "capture_datetime": "2026:03:14 12:34:56",
        "camera_make": "RapidCull",
        "camera_model": "FixtureCam",
    }
    assert expected.items() <= metadata.items()


@pytest.mark.fr
@pytest.mark.integration
def test_fr_002c_real_exiftool_batch_mode_maps_multiple_assets_deterministically(
    tmp_path: Path,
) -> None:
    if shutil.which("exiftool") is None:
        pytest.fail("Missing required system dependency: exiftool")

    first = tmp_path / "first.jpg"
    second = tmp_path / "second.jpg"
    _write_tiny_jpeg(first)
    _write_tiny_jpeg(second)

    _write_exif(
        path=first,
        create_date="2026:03:14 10:00:00",
        make="RapidCull",
        model="FirstCam",
    )
    _write_exif(
        path=second,
        create_date="2026:03:14 11:00:00",
        make="RapidCull",
        model="SecondCam",
    )

    with RealExifToolBatchExtractor() as extractor:
        result = extract_metadata_for_ingest(paths=[second, first], extractor=extractor)

    assert list(result.metadata_by_path.keys()) == [first.resolve(), second.resolve()]
    assert result.failed_items == []

    first_metadata = result.metadata_by_path[first.resolve()]
    second_metadata = result.metadata_by_path[second.resolve()]

    expected_first = {
        "file_type": "JPEG",
        "capture_datetime": "2026:03:14 10:00:00",
        "camera_make": "RapidCull",
        "camera_model": "FirstCam",
    }
    assert expected_first.items() <= first_metadata.items()
    expected_second = {
        "file_type": "JPEG",
        "capture_datetime": "2026:03:14 11:00:00",
        "camera_make": "RapidCull",
        "camera_model": "SecondCam",
    }
    assert expected_second.items() <= second_metadata.items()
