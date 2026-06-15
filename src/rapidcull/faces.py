from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path

from rapidcull.adapters.insightface_adapter import (
    FaceDetectionFailure,
    FaceDetectionSuccess,
    FaceDetector,
)
from rapidcull.models import FaceDetectionResult, FaceRecord, FailedIngestItem


def _generate_face_id(image_id: str, bbox_x: int, bbox_y: int, bbox_w: int, bbox_h: int) -> str:
    key = f"{image_id}:{bbox_x}:{bbox_y}:{bbox_w}:{bbox_h}"
    return hashlib.sha1(key.encode()).hexdigest()


def _lookup_image_id(db_path: Path, path: str) -> str | None:
    with sqlite3.connect(db_path) as conn:
        row = conn.execute("SELECT image_id FROM images WHERE path = ?", (path,)).fetchone()
    return str(row[0]) if row else None


def _faces_already_stored(db_path: Path, image_id: str) -> bool:
    with sqlite3.connect(db_path) as conn:
        row = conn.execute("SELECT 1 FROM faces WHERE image_id = ? LIMIT 1", (image_id,)).fetchone()
    return row is not None


def _store_faces(
    db_path: Path,
    image_id: str,
    outcome: FaceDetectionSuccess,
) -> None:
    rows = []
    for face in outcome.faces:
        face_id = _generate_face_id(image_id, face.bbox_x, face.bbox_y, face.bbox_w, face.bbox_h)
        rows.append(
            (
                face_id,
                image_id,
                None,
                face.embedding,
                face.bbox_x,
                face.bbox_y,
                face.bbox_w,
                face.bbox_h,
                face.detection_score,
            )
        )
    with sqlite3.connect(db_path) as conn:
        conn.executemany(
            """
            INSERT OR IGNORE INTO faces
              (face_id, image_id, person_id, embedding,
               bbox_x, bbox_y, bbox_w, bbox_h, detection_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )
        conn.commit()


def detect_and_store_faces(
    db_path: Path,
    image_paths: list[Path],
    detector: FaceDetector,
) -> FaceDetectionResult:
    processed = 0
    skipped = 0
    failed = 0
    failed_items: list[FailedIngestItem] = []

    for path in sorted(image_paths):
        image_id = _lookup_image_id(db_path, str(path))
        if image_id is None:
            skipped += 1
            continue

        if _faces_already_stored(db_path, image_id):
            skipped += 1
            continue

        outcome = detector.detect(path)

        if isinstance(outcome, FaceDetectionFailure):
            failed += 1
            failed_items.append(FailedIngestItem(path=str(path), reason=outcome.reason))
            continue

        _store_faces(db_path, image_id, outcome)
        processed += 1

    return FaceDetectionResult(
        processed_count=processed,
        skipped_count=skipped,
        failed_count=failed,
        failed_items=failed_items,
    )


def get_faces_for_image(db_path: Path, image_id: str) -> list[FaceRecord]:
    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT face_id, image_id, person_id, embedding,
                   bbox_x, bbox_y, bbox_w, bbox_h, detection_score
            FROM faces
            WHERE image_id = ?
            ORDER BY face_id
            """,
            (image_id,),
        ).fetchall()
    return [
        FaceRecord(
            face_id=row[0],
            image_id=row[1],
            person_id=row[2],
            embedding=bytes(row[3]),
            bbox_x=row[4],
            bbox_y=row[5],
            bbox_w=row[6],
            bbox_h=row[7],
            detection_score=row[8],
        )
        for row in rows
    ]
