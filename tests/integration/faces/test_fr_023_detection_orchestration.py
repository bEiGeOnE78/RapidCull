"""Integration tests for FR-023: Face detection orchestration and DB storage."""

from __future__ import annotations

import sqlite3
import struct
from pathlib import Path

import pytest

from rapidcull.adapters.insightface_adapter import (
    DetectedFace,
    FaceDetectionFailure,
    FaceDetectionSuccess,
)
from rapidcull.faces import detect_and_store_faces, get_faces_for_image
from rapidcull.identity import create_image_record
from rapidcull.models import FaceDetectionResult, FaceRecord
from rapidcull.schema import create_or_validate_schema


def _make_embedding(value: float = 0.5, dims: int = 512) -> bytes:
    return struct.pack(f"{dims}f", *[value] * dims)


def _stub_success(n_faces: int = 1) -> FaceDetectionSuccess:
    faces = [
        DetectedFace(
            bbox_x=i * 10,
            bbox_y=0,
            bbox_w=80,
            bbox_h=100,
            embedding=_make_embedding(float(i) / 10),
            detection_score=0.9,
        )
        for i in range(n_faces)
    ]
    return FaceDetectionSuccess(faces=faces)


class _StubDetector:
    def __init__(self, outcomes: dict[str, FaceDetectionSuccess | FaceDetectionFailure]) -> None:
        self._outcomes = outcomes

    def detect(self, image_path: Path) -> FaceDetectionSuccess | FaceDetectionFailure:
        return self._outcomes.get(
            str(image_path), FaceDetectionFailure(reason="face_detection_failed")
        )

    @property
    def pipeline_available(self) -> bool:
        return True


@pytest.fixture()
def db_path(tmp_path: Path) -> Path:
    path = tmp_path / "test.db"
    create_or_validate_schema(path)
    return path


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


@pytest.mark.fr
@pytest.mark.integration
def test_fr_023_detect_and_store_happy_path(db_path: Path, tmp_path: Path) -> None:
    """Detected faces stored in DB; result has correct accounting."""
    img1 = tmp_path / "a.jpg"
    img2 = tmp_path / "b.jpg"
    img1.write_bytes(b"\xff\xd8\xff")
    img2.write_bytes(b"\xff\xd8\xff")

    create_image_record(db_path, img1)
    create_image_record(db_path, img2)

    detector = _StubDetector(
        {
            str(img1): _stub_success(2),
            str(img2): _stub_success(1),
        }
    )

    result = detect_and_store_faces(db_path, [img1, img2], detector=detector)

    assert isinstance(result, FaceDetectionResult)
    assert result.processed_count == 2
    assert result.skipped_count == 0
    assert result.failed_count == 0
    assert result.failed_items == []

    faces1 = get_faces_for_image(db_path, _image_id_for(db_path, str(img1)))
    faces2 = get_faces_for_image(db_path, _image_id_for(db_path, str(img2)))
    assert len(faces1) == 2
    assert len(faces2) == 1


@pytest.mark.fr
@pytest.mark.integration
def test_fr_023_detect_and_store_idempotent(db_path: Path, tmp_path: Path) -> None:
    """Running detection twice on same image skips on second run."""
    img = tmp_path / "a.jpg"
    img.write_bytes(b"\xff\xd8\xff")
    create_image_record(db_path, img)

    detector = _StubDetector({str(img): _stub_success(1)})

    result1 = detect_and_store_faces(db_path, [img], detector=detector)
    result2 = detect_and_store_faces(db_path, [img], detector=detector)

    assert result1.processed_count == 1
    assert result2.skipped_count == 1
    assert result2.processed_count == 0


@pytest.mark.fr
@pytest.mark.integration
def test_fr_023_detect_and_store_skips_unregistered_image(db_path: Path, tmp_path: Path) -> None:
    """Image not in DB (no image_id) skipped with canonical reason."""
    img = tmp_path / "orphan.jpg"
    img.write_bytes(b"\xff\xd8\xff")

    detector = _StubDetector({str(img): _stub_success(1)})
    result = detect_and_store_faces(db_path, [img], detector=detector)

    assert result.skipped_count == 1
    assert result.processed_count == 0


@pytest.mark.fr
@pytest.mark.integration
def test_fr_023_detect_and_store_continue_on_error(db_path: Path, tmp_path: Path) -> None:
    """Adapter failure for one image does not abort remaining images."""
    good = tmp_path / "good.jpg"
    bad = tmp_path / "bad.jpg"
    good.write_bytes(b"\xff\xd8\xff")
    bad.write_bytes(b"\xff\xd8\xff")

    create_image_record(db_path, good)
    create_image_record(db_path, bad)

    detector = _StubDetector(
        {
            str(good): _stub_success(1),
            str(bad): FaceDetectionFailure(reason="face_detection_failed"),
        }
    )

    result = detect_and_store_faces(db_path, [good, bad], detector=detector)

    assert result.processed_count == 1
    assert result.failed_count == 1
    assert len(result.failed_items) == 1
    assert result.failed_items[0].reason == "face_detection_failed"


@pytest.mark.fr
@pytest.mark.integration
def test_fr_023_embedding_roundtrip(db_path: Path, tmp_path: Path) -> None:
    """Embedding stored as bytes and retrieved identically."""
    img = tmp_path / "a.jpg"
    img.write_bytes(b"\xff\xd8\xff")
    create_image_record(db_path, img)

    embedding = _make_embedding(0.42)
    detector = _StubDetector(
        {
            str(img): FaceDetectionSuccess(
                faces=[
                    DetectedFace(
                        bbox_x=5,
                        bbox_y=10,
                        bbox_w=50,
                        bbox_h=60,
                        embedding=embedding,
                        detection_score=0.95,
                    ),
                ]
            )
        }
    )

    detect_and_store_faces(db_path, [img], detector=detector)

    image_id = _image_id_for(db_path, str(img))
    faces = get_faces_for_image(db_path, image_id)
    assert len(faces) == 1
    assert faces[0].embedding == embedding


@pytest.mark.fr
@pytest.mark.integration
def test_fr_023_get_faces_returns_face_records(db_path: Path, tmp_path: Path) -> None:
    """get_faces_for_image returns list of FaceRecord with all fields populated."""
    img = tmp_path / "a.jpg"
    img.write_bytes(b"\xff\xd8\xff")
    create_image_record(db_path, img)

    detector = _StubDetector({str(img): _stub_success(1)})
    detect_and_store_faces(db_path, [img], detector=detector)

    image_id = _image_id_for(db_path, str(img))
    faces = get_faces_for_image(db_path, image_id)

    assert len(faces) == 1
    face = faces[0]
    assert isinstance(face, FaceRecord)
    assert face.image_id == image_id
    assert face.person_id is None
    assert face.bbox_w == 80
    assert face.detection_score == pytest.approx(0.9)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _image_id_for(db_path: Path, path: str) -> str:
    with sqlite3.connect(db_path) as conn:
        row = conn.execute("SELECT image_id FROM images WHERE path = ?", (path,)).fetchone()
    assert row is not None, f"No image_id for {path}"
    return str(row[0])
