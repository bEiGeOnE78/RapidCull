from __future__ import annotations

import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol, runtime_checkable


@dataclass(frozen=True)
class DetectedFace:
    bbox_x: int
    bbox_y: int
    bbox_w: int
    bbox_h: int
    embedding: bytes  # 512 float32s serialized via struct.pack
    detection_score: float


@dataclass(frozen=True)
class FaceDetectionSuccess:
    faces: list[DetectedFace]


@dataclass(frozen=True)
class FaceDetectionFailure:
    reason: str


FaceDetectionOutcome = FaceDetectionSuccess | FaceDetectionFailure


@runtime_checkable
class FaceDetector(Protocol):
    def detect(self, image_path: Path) -> FaceDetectionOutcome: ...

    @property
    def pipeline_available(self) -> bool: ...


def _insightface_available() -> bool:
    try:
        import insightface  # noqa: F401

        return True
    except ImportError:
        return False


class InsightFaceAdapter:
    def __init__(self, _force_unavailable: bool = False) -> None:
        self._force_unavailable = _force_unavailable
        self._model: Any | None = None

    @property
    def pipeline_available(self) -> bool:
        if self._force_unavailable:
            return False
        return _insightface_available()

    def _get_model(self) -> Any:
        if self._model is None:
            import insightface  # noqa: PLC0415

            app = insightface.app.FaceAnalysis(
                name="buffalo_sc",
                providers=["CPUExecutionProvider"],
            )
            app.prepare(ctx_id=0, det_size=(640, 640))
            self._model = app
        return self._model

    def detect(self, image_path: Path) -> FaceDetectionOutcome:
        if not self.pipeline_available:
            return FaceDetectionFailure(reason="face_detection_pipeline_unavailable")

        if not image_path.exists():
            return FaceDetectionFailure(reason="face_detection_pipeline_unavailable")

        try:
            import cv2  # noqa: PLC0415

            img = cv2.imread(str(image_path))
            if img is None:
                return FaceDetectionFailure(reason="face_detection_image_unreadable")

            app = self._get_model()
            raw_faces = app.get(img)

            faces: list[DetectedFace] = []
            for face in raw_faces:
                box = face.bbox.astype(int)
                x1, y1, x2, y2 = int(box[0]), int(box[1]), int(box[2]), int(box[3])
                w = x2 - x1
                h = y2 - y1
                embedding_bytes = struct.pack(f"{len(face.embedding)}f", *face.embedding.tolist())
                faces.append(
                    DetectedFace(
                        bbox_x=x1,
                        bbox_y=y1,
                        bbox_w=w,
                        bbox_h=h,
                        embedding=embedding_bytes,
                        detection_score=float(face.det_score),
                    )
                )
            return FaceDetectionSuccess(faces=faces)

        except Exception:
            return FaceDetectionFailure(reason="face_detection_failed")
