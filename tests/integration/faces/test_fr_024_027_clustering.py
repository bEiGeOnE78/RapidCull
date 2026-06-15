"""Integration tests for FR-024, FR-027: Face clustering and re-cluster modes."""

from __future__ import annotations

import sqlite3
import struct
from pathlib import Path

import pytest

from rapidcull.adapters.insightface_adapter import DetectedFace, FaceDetectionSuccess
from rapidcull.faces import cluster_faces, detect_and_store_faces, get_faces_for_image
from rapidcull.identity import create_image_record
from rapidcull.models import ClusterMode, FaceClusterResult
from rapidcull.schema import create_or_validate_schema

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_embedding(seed: float, dims: int = 512) -> bytes:
    """Deterministic embedding: all dims set to seed value."""
    return struct.pack(f"{dims}f", *[seed] * dims)


class _ConstDetector:
    """Stub detector returning a fixed set of faces for every image."""

    def __init__(self, faces: list[DetectedFace]) -> None:
        self._faces = faces

    def detect(self, image_path: Path) -> FaceDetectionSuccess:
        return FaceDetectionSuccess(faces=self._faces)

    @property
    def pipeline_available(self) -> bool:
        return True


def _register_and_detect(
    db_path: Path,
    img_path: Path,
    embedding_seed: float,
) -> None:
    create_image_record(db_path, img_path)
    detector = _ConstDetector(
        [
            DetectedFace(
                bbox_x=0,
                bbox_y=0,
                bbox_w=80,
                bbox_h=100,
                embedding=_make_embedding(embedding_seed),
                detection_score=0.95,
            )
        ]
    )
    detect_and_store_faces(db_path, [img_path], detector=detector)


@pytest.fixture()
def db_path(tmp_path: Path) -> Path:
    path = tmp_path / "test.db"
    create_or_validate_schema(path)
    return path


# ---------------------------------------------------------------------------
# FaceClusterResult model
# ---------------------------------------------------------------------------


@pytest.mark.fr
@pytest.mark.integration
def test_fr_024_cluster_result_model() -> None:
    """FaceClusterResult is a frozen dataclass with expected fields."""
    result = FaceClusterResult(
        person_count=3,
        assigned_count=10,
        noise_count=2,
    )
    assert result.person_count == 3
    assert result.assigned_count == 10
    assert result.noise_count == 2


# ---------------------------------------------------------------------------
# ClusterMode enum
# ---------------------------------------------------------------------------


@pytest.mark.fr
@pytest.mark.integration
def test_fr_027_cluster_mode_values() -> None:
    """ClusterMode has ALL and NEW_ONLY variants."""
    assert ClusterMode.ALL is not None
    assert ClusterMode.NEW_ONLY is not None


# ---------------------------------------------------------------------------
# Basic clustering — tight clusters
# ---------------------------------------------------------------------------


@pytest.mark.fr
@pytest.mark.integration
def test_fr_024_cluster_groups_similar_faces(db_path: Path, tmp_path: Path) -> None:
    """Two faces with identical embeddings land in same cluster → 1 person."""
    img1 = tmp_path / "a.jpg"
    img2 = tmp_path / "b.jpg"
    img1.write_bytes(b"\xff\xd8\xff")
    img2.write_bytes(b"\xff\xd8\xff")

    _register_and_detect(db_path, img1, embedding_seed=0.1)
    _register_and_detect(db_path, img2, embedding_seed=0.1)  # same seed = same face

    result = cluster_faces(db_path, mode=ClusterMode.ALL)

    assert isinstance(result, FaceClusterResult)
    assert result.person_count == 1
    assert result.assigned_count == 2
    assert result.noise_count == 0


@pytest.mark.fr
@pytest.mark.integration
def test_fr_024_cluster_separates_distinct_faces(db_path: Path, tmp_path: Path) -> None:
    """Two faces with maximally different embeddings land in separate clusters → 2 persons."""
    img1 = tmp_path / "a.jpg"
    img2 = tmp_path / "b.jpg"
    img1.write_bytes(b"\xff\xd8\xff")
    img2.write_bytes(b"\xff\xd8\xff")

    _register_and_detect(db_path, img1, embedding_seed=0.0)  # all zeros
    _register_and_detect(db_path, img2, embedding_seed=1.0)  # all ones

    result = cluster_faces(
        db_path,
        mode=ClusterMode.ALL,
        distance_threshold=0.1,  # tight: only near-identical vectors cluster
        min_samples=1,
    )

    assert result.person_count == 2
    assert result.assigned_count == 2
    assert result.noise_count == 0


@pytest.mark.fr
@pytest.mark.integration
def test_fr_024_noise_faces_not_assigned(db_path: Path, tmp_path: Path) -> None:
    """Isolated face (no neighbours) with min_samples=2 becomes noise (person_id=NULL)."""
    img = tmp_path / "a.jpg"
    img.write_bytes(b"\xff\xd8\xff")
    _register_and_detect(db_path, img, embedding_seed=0.5)

    result = cluster_faces(
        db_path,
        mode=ClusterMode.ALL,
        distance_threshold=0.05,
        min_samples=2,  # need 2 neighbours — only 1 face → noise
    )

    assert result.noise_count == 1
    assert result.assigned_count == 0
    assert result.person_count == 0

    # Verify DB: person_id is NULL
    with sqlite3.connect(db_path) as conn:
        row = conn.execute("SELECT person_id FROM faces LIMIT 1").fetchone()
    assert row is not None
    assert row[0] is None


# ---------------------------------------------------------------------------
# NEW_ONLY mode
# ---------------------------------------------------------------------------


@pytest.mark.fr
@pytest.mark.integration
def test_fr_027_new_only_skips_already_assigned(db_path: Path, tmp_path: Path) -> None:
    """NEW_ONLY mode leaves already-assigned faces untouched."""
    img1 = tmp_path / "a.jpg"
    img2 = tmp_path / "b.jpg"
    img1.write_bytes(b"\xff\xd8\xff")
    img2.write_bytes(b"\xff\xd8\xff")

    _register_and_detect(db_path, img1, embedding_seed=0.1)
    _register_and_detect(db_path, img2, embedding_seed=0.1)

    # First run — ALL mode assigns both
    result_all = cluster_faces(db_path, mode=ClusterMode.ALL, min_samples=1)
    assert result_all.assigned_count == 2

    # Record the person_id assigned to img1's face
    img1_id = _image_id_for(db_path, str(img1.resolve()))
    faces_before = get_faces_for_image(db_path, img1_id)
    person_id_before = faces_before[0].person_id

    # Second run — NEW_ONLY: already-assigned face not touched
    result_new = cluster_faces(db_path, mode=ClusterMode.NEW_ONLY, min_samples=1)

    faces_after = get_faces_for_image(db_path, img1_id)
    assert faces_after[0].person_id == person_id_before  # unchanged
    assert result_new.assigned_count == 0  # nothing new to assign


@pytest.mark.fr
@pytest.mark.integration
def test_fr_027_all_mode_resets_assignments(db_path: Path, tmp_path: Path) -> None:
    """ALL mode reassigns all faces, potentially changing cluster membership."""
    img1 = tmp_path / "a.jpg"
    img2 = tmp_path / "b.jpg"
    img1.write_bytes(b"\xff\xd8\xff")
    img2.write_bytes(b"\xff\xd8\xff")

    _register_and_detect(db_path, img1, embedding_seed=0.1)
    _register_and_detect(db_path, img2, embedding_seed=0.1)

    # First run
    cluster_faces(db_path, mode=ClusterMode.ALL, min_samples=1)

    # Second ALL run — idempotent on same data
    result = cluster_faces(db_path, mode=ClusterMode.ALL, min_samples=1)
    assert result.person_count >= 1
    assert result.assigned_count == 2


# ---------------------------------------------------------------------------
# persons table
# ---------------------------------------------------------------------------


@pytest.mark.fr
@pytest.mark.integration
def test_fr_024_persons_created_in_db(db_path: Path, tmp_path: Path) -> None:
    """Clustering inserts person rows into persons table."""
    img1 = tmp_path / "a.jpg"
    img2 = tmp_path / "b.jpg"
    img1.write_bytes(b"\xff\xd8\xff")
    img2.write_bytes(b"\xff\xd8\xff")

    _register_and_detect(db_path, img1, embedding_seed=0.2)
    _register_and_detect(db_path, img2, embedding_seed=0.8)

    cluster_faces(
        db_path,
        mode=ClusterMode.ALL,
        distance_threshold=0.1,
        min_samples=1,
    )

    with sqlite3.connect(db_path) as conn:
        count = conn.execute("SELECT COUNT(*) FROM persons").fetchone()[0]
    assert count >= 1


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _image_id_for(db_path: Path, path: str) -> str:
    with sqlite3.connect(db_path) as conn:
        row = conn.execute("SELECT image_id FROM images WHERE path = ?", (path,)).fetchone()
    assert row is not None
    return str(row[0])
