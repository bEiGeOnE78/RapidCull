"""Helper: render a 96×96 WebP crop of the best face for a person.

Cache location: <library_root>/.rapidcull/face_thumbs/<face_id>.webp
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Optional


def render_person_thumbnail(
    db_path: Path,
    person_id: str,
    library_root: Path,
) -> Optional[Path]:
    """Return path to a cached 96×96 WebP face crop for *person_id*.

    Picks the face with the highest detection_score for the person.
    Returns None if no faces are assigned to this person.
    """
    try:
        import cv2
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("cv2 (opencv-python) is required for face thumbnails") from exc

    # 1. Query best face + image path for person.
    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            """
            SELECT f.face_id,
                   COALESCE(i.display_path, i.path) AS img_path,
                   f.bbox_x, f.bbox_y, f.bbox_w, f.bbox_h
            FROM faces f
            JOIN images i ON i.image_id = f.image_id
            WHERE f.person_id = ?
            ORDER BY f.detection_score DESC
            LIMIT 1
            """,
            (person_id,),
        ).fetchone()

    if row is None:
        return None

    face_id: str = row[0]
    img_path_str: str = row[1]
    bbox_x: int = int(row[2])
    bbox_y: int = int(row[3])
    bbox_w: int = int(row[4])
    bbox_h: int = int(row[5])

    # 2. Check cache.
    cache_dir = library_root / ".rapidcull" / "face_thumbs"
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_path = cache_dir / f"{face_id}.webp"
    if cache_path.exists():
        return cache_path

    # 3. Load image and crop.
    image = cv2.imread(str(img_path_str))
    if image is None:
        return None  # image file unreadable

    img_h, img_w = image.shape[:2]

    # 20% margin around bbox, clamped to image bounds.
    margin_x = int(bbox_w * 0.20)
    margin_y = int(bbox_h * 0.20)
    x1 = max(0, bbox_x - margin_x)
    y1 = max(0, bbox_y - margin_y)
    x2 = min(img_w, bbox_x + bbox_w + margin_x)
    y2 = min(img_h, bbox_y + bbox_h + margin_y)

    crop = image[y1:y2, x1:x2]
    if crop.size == 0:
        return None

    # 4. Resize to 96×96 and write WebP.
    thumb = cv2.resize(crop, (96, 96), interpolation=cv2.INTER_AREA)
    ok = cv2.imwrite(str(cache_path), thumb, [cv2.IMWRITE_WEBP_QUALITY, 85])
    if not ok:
        return None  # pragma: no cover

    return cache_path
