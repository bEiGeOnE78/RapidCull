from __future__ import annotations

import hashlib
import sqlite3
import uuid
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
from sklearn.cluster import DBSCAN

from rapidcull.adapters.insightface_adapter import (
    FaceDetectionFailure,
    FaceDetectionSuccess,
    FaceDetector,
)
from rapidcull.models import (
    ClusterMode,
    FaceClusterResult,
    FaceDetectionResult,
    FaceRecord,
    FailedIngestItem,
)


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
    image_paths: list[tuple[Path, Path]] | list[Path],
    detector: FaceDetector,
) -> FaceDetectionResult:
    processed = 0
    skipped = 0
    failed = 0
    failed_items: list[FailedIngestItem] = []

    # Normalise: accept either plain paths or (db_path, decode_path) pairs.
    pairs: list[tuple[Path, Path]] = [
        (p, p) if isinstance(p, Path) else p
        for p in image_paths
    ]

    for db_img_path, decode_path in sorted(pairs, key=lambda t: t[0]):
        image_id = _lookup_image_id(db_path, str(db_img_path))
        if image_id is None:
            skipped += 1
            continue

        if _faces_already_stored(db_path, image_id):
            skipped += 1
            continue

        outcome = detector.detect(decode_path)

        if isinstance(outcome, FaceDetectionFailure):
            failed += 1
            failed_items.append(FailedIngestItem(path=str(db_img_path), reason=outcome.reason))
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


def cluster_faces(
    db_path: Path,
    mode: ClusterMode | None = None,
    distance_threshold: float = 0.4,
    min_samples: int = 2,
) -> FaceClusterResult:
    if mode is None:
        mode = ClusterMode.ALL

    with sqlite3.connect(db_path) as conn:
        if mode == ClusterMode.NEW_ONLY:
            rows = conn.execute(
                "SELECT face_id, embedding FROM faces WHERE person_id IS NULL ORDER BY face_id"
            ).fetchall()
        else:
            # ALL mode: clear existing assignments first
            conn.execute("UPDATE faces SET person_id = NULL")
            conn.commit()
            rows = conn.execute("SELECT face_id, embedding FROM faces ORDER BY face_id").fetchall()

    if not rows:
        return FaceClusterResult(person_count=0, assigned_count=0, noise_count=0)

    face_ids = [row[0] for row in rows]
    embeddings = np.array(
        [np.frombuffer(bytes(row[1]), dtype=np.float32) for row in rows],
        dtype=np.float32,
    )

    clustering = DBSCAN(
        eps=distance_threshold,
        min_samples=min_samples,
        metric="cosine",
    ).fit(embeddings)

    labels: list[int] = clustering.labels_.tolist()

    # Map cluster label → person_id (create new persons as needed)
    label_to_person: dict[int, str] = {}
    now = datetime.now(UTC).isoformat()

    with sqlite3.connect(db_path) as conn:
        for label, face_id in zip(labels, face_ids, strict=True):
            if label == -1:
                continue  # noise — leave person_id NULL
            if label not in label_to_person:
                person_id = str(uuid.uuid4())
                conn.execute(
                    "INSERT OR IGNORE INTO persons (person_id, name, created_at) VALUES (?, ?, ?)",
                    (person_id, f"Person {label + 1}", now),
                )
                label_to_person[label] = person_id
            conn.execute(
                "UPDATE faces SET person_id = ? WHERE face_id = ?",
                (label_to_person[label], face_id),
            )
        conn.commit()

    assigned = sum(1 for lbl in labels if lbl != -1)
    noise = sum(1 for lbl in labels if lbl == -1)

    return FaceClusterResult(
        person_count=len(label_to_person),
        assigned_count=assigned,
        noise_count=noise,
    )
