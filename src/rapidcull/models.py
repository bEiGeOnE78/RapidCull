from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TypeAlias

MetadataValue: TypeAlias = str | int | float | bool | None
ToolReasonCounts: TypeAlias = dict[str, int]
ToolStats: TypeAlias = dict[str, int | ToolReasonCounts]
ProxyToolSummary: TypeAlias = dict[str, ToolStats]


@dataclass(frozen=True)
class IngestPlan:
    to_process: list[Path]
    skipped: list[Path]


@dataclass(frozen=True)
class ImageRecord:
    image_id: str
    path: str


@dataclass(frozen=True)
class FailedIngestItem:
    path: str
    reason: str


@dataclass(frozen=True)
class IngestRunSummary:
    processed_count: int
    skipped_count: int
    failed_count: int
    failed_items: list[FailedIngestItem]


@dataclass(frozen=True)
class IngestMetadataExtractionResult:
    metadata_by_path: dict[Path, dict[str, MetadataValue]]
    failed_items: list[FailedIngestItem]


@dataclass(frozen=True)
class ProxyGenerationPlan:
    thumbnail_targets: list[Path]
    heic_display_proxy_targets: list[Path]
    raw_proxy_targets: list[Path]


@dataclass(frozen=True)
class GeneratedProxy:
    source_path: str
    proxy_kind: str


@dataclass(frozen=True)
class ProxyGenerationResult:
    generated: list[GeneratedProxy]
    failed: list[FailedIngestItem]
    processed_count: int = 0
    skipped_count: int = 0
    failed_count: int = 0
    elapsed_ms: int = 0
    tool_summary: ProxyToolSummary = field(default_factory=dict)


@dataclass(frozen=True)
class RegenerationSelectionResult:
    selected_paths: list[str]
    invalid_ids: list[str]
    mode: str


@dataclass(frozen=True)
class OrphanCleanupReport:
    deleted_count: int
    deleted_paths: list[str]


@dataclass(frozen=True)
class GalleryFailedItem:
    path: str
    reason: str


@dataclass(frozen=True)
class GalleryCreationResult:
    gallery_path: str
    created_paths: list[str]
    skipped_paths: list[str]
    failed_items: list[GalleryFailedItem]


@dataclass(frozen=True)
class GalleryMetadataRebuildResult:
    gallery_path: str
    metadata_path: str
    asset_count: int


@dataclass(frozen=True)
class GalleryMetadataRebuildSummary:
    rebuilt: list[GalleryMetadataRebuildResult]


@dataclass(frozen=True)
class GalleryRenameResult:
    ok: bool
    old_gallery_path: str
    new_gallery_path: str | None
    error: GalleryMutationError | None


@dataclass(frozen=True)
class GalleryDeleteResult:
    ok: bool
    gallery_path: str
    error: GalleryMutationError | None


@dataclass(frozen=True)
class GalleryMutationError:
    code: str
    message: str
    path: str


@dataclass(frozen=True)
class GalleriesIndexEntry:
    gallery_path: str
    asset_count: int
    assets: list[str]


@dataclass(frozen=True)
class GalleriesIndexFailure:
    gallery_path: str
    reason: str


@dataclass(frozen=True)
class GalleriesIndexRebuildResult:
    index_path: str
    gallery_count: int
    processed_count: int
    skipped_count: int
    failed_count: int
    failures: list[GalleriesIndexFailure]


@dataclass(frozen=True)
class CollectionQueryResult:
    matching_ids: list[str]
    total_count: int
    query_expression_text: str


@dataclass(frozen=True)
class FaceRecord:
    face_id: str
    image_id: str
    person_id: str | None
    embedding: bytes
    bbox_x: int
    bbox_y: int
    bbox_w: int
    bbox_h: int
    detection_score: float


@dataclass(frozen=True)
class PersonRecord:
    person_id: str
    name: str
    created_at: str


@dataclass(frozen=True)
class FaceDetectionResult:
    processed_count: int
    skipped_count: int
    failed_count: int
    failed_items: list[FailedIngestItem]
