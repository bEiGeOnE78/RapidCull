"""Integration tests for FR-023: Face detection adapter seam."""

from __future__ import annotations

import struct
from pathlib import Path

import pytest

from rapidcull.adapters.insightface_adapter import (
    DetectedFace,
    FaceDetectionFailure,
    FaceDetectionOutcome,
    FaceDetectionSuccess,
    FaceDetector,
    InsightFaceAdapter,
)

# ---------------------------------------------------------------------------
# Test double — protocol-based, injectable in orchestration tests
# ---------------------------------------------------------------------------


class _StubFaceDetector:
    """Minimal test double implementing FaceDetector protocol."""

    def __init__(self, outcome: FaceDetectionOutcome, available: bool = True) -> None:
        self._outcome = outcome
        self._available = available

    def detect(self, image_path: Path) -> FaceDetectionOutcome:
        return self._outcome

    @property
    def pipeline_available(self) -> bool:
        return self._available


def _make_embedding(dims: int = 512) -> bytes:
    """Create a deterministic fake embedding of the given dimensionality."""
    return struct.pack(f"{dims}f", *[float(i % 256) / 255.0 for i in range(dims)])


# ---------------------------------------------------------------------------
# Protocol conformance
# ---------------------------------------------------------------------------


@pytest.mark.fr
@pytest.mark.integration
def test_fr_023_stub_conforms_to_face_detector_protocol() -> None:
    """Test double must satisfy FaceDetector protocol (type-checked at runtime)."""
    embedding = _make_embedding()
    face = DetectedFace(
        bbox_x=10,
        bbox_y=20,
        bbox_w=80,
        bbox_h=100,
        embedding=embedding,
        detection_score=0.97,
    )
    outcome = FaceDetectionSuccess(faces=[face])
    stub: FaceDetector = _StubFaceDetector(outcome=outcome)
    assert stub.pipeline_available is True
    result = stub.detect(Path("/fake/image.jpg"))
    assert isinstance(result, FaceDetectionSuccess)
    assert len(result.faces) == 1


@pytest.mark.fr
@pytest.mark.integration
def test_fr_023_stub_failure_conforms_to_protocol() -> None:
    """Test double returning failure satisfies FaceDetector protocol."""
    outcome = FaceDetectionFailure(reason="face_detection_failed")
    stub: FaceDetector = _StubFaceDetector(outcome=outcome, available=False)
    assert stub.pipeline_available is False
    result = stub.detect(Path("/fake/image.jpg"))
    assert isinstance(result, FaceDetectionFailure)


# ---------------------------------------------------------------------------
# DetectedFace model
# ---------------------------------------------------------------------------


@pytest.mark.fr
@pytest.mark.integration
def test_fr_023_detected_face_is_frozen_dataclass() -> None:
    """DetectedFace is a frozen dataclass with correct fields."""
    embedding = _make_embedding()
    face = DetectedFace(
        bbox_x=0,
        bbox_y=0,
        bbox_w=100,
        bbox_h=120,
        embedding=embedding,
        detection_score=0.95,
    )
    assert face.bbox_x == 0
    assert face.bbox_w == 100
    assert len(face.embedding) == 512 * 4  # 512 float32s = 2048 bytes
    assert face.detection_score == pytest.approx(0.95)

    with pytest.raises(AttributeError):
        face.bbox_x = 99  # type: ignore[misc]


@pytest.mark.fr
@pytest.mark.integration
def test_fr_023_face_detection_success_holds_list() -> None:
    """FaceDetectionSuccess holds a list of DetectedFace."""
    faces = [
        DetectedFace(
            bbox_x=0,
            bbox_y=0,
            bbox_w=50,
            bbox_h=60,
            embedding=_make_embedding(),
            detection_score=0.9,
        ),
        DetectedFace(
            bbox_x=100,
            bbox_y=10,
            bbox_w=60,
            bbox_h=70,
            embedding=_make_embedding(),
            detection_score=0.85,
        ),
    ]
    result = FaceDetectionSuccess(faces=faces)
    assert len(result.faces) == 2


@pytest.mark.fr
@pytest.mark.integration
def test_fr_023_face_detection_failure_has_reason() -> None:
    """FaceDetectionFailure carries a canonical reason string."""
    result = FaceDetectionFailure(reason="face_detection_image_unreadable")
    assert result.reason == "face_detection_image_unreadable"


# ---------------------------------------------------------------------------
# InsightFaceAdapter.pipeline_available
# ---------------------------------------------------------------------------


@pytest.mark.fr
@pytest.mark.integration
def test_fr_023_adapter_pipeline_available_reflects_import() -> None:
    """pipeline_available returns True iff insightface is importable."""
    adapter = InsightFaceAdapter()
    try:
        import insightface  # noqa: F401

        assert adapter.pipeline_available is True
    except ImportError:
        assert adapter.pipeline_available is False


# ---------------------------------------------------------------------------
# InsightFaceAdapter.detect — unavailable path
# ---------------------------------------------------------------------------


@pytest.mark.fr
@pytest.mark.integration
def test_fr_023_adapter_detect_returns_failure_when_unavailable(
    tmp_path: Path,
) -> None:
    """detect() returns FaceDetectionFailure when pipeline_available is False."""
    adapter = InsightFaceAdapter(_force_unavailable=True)
    img = tmp_path / "photo.jpg"
    img.write_bytes(b"\xff\xd8\xff")  # minimal JPEG header

    result = adapter.detect(img)
    assert isinstance(result, FaceDetectionFailure)
    assert "unavailable" in result.reason


@pytest.mark.fr
@pytest.mark.integration
def test_fr_023_adapter_detect_returns_failure_on_missing_file(
    tmp_path: Path,
) -> None:
    """detect() returns FaceDetectionFailure when image path does not exist."""
    adapter = InsightFaceAdapter(_force_unavailable=True)
    result = adapter.detect(tmp_path / "nonexistent.jpg")
    assert isinstance(result, FaceDetectionFailure)
