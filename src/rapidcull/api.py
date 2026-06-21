from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from rapidcull.api_envelope import ApiError, ok, register_handlers
from rapidcull.collections import Collection
from rapidcull.query_grammar import parse_query
from rapidcull.schema import (
    CURRENT_SCHEMA_VERSION,
    SchemaVersionMismatchError,
    create_or_validate_schema,
    get_schema_version,
)

logger = logging.getLogger(__name__)


class QueryRequest(BaseModel):
    query_text: str


def create_app(db_path: Path | None = None, library_root: Path | None = None) -> FastAPI:
    """Create a FastAPI application instance with optional DB path for face endpoints."""
    from rapidcull import api_galleries, api_images, api_persons, api_trash  # noqa: PLC0415
    from rapidcull.api_jobs import router as jobs_router_  # noqa: PLC0415
    from rapidcull.security import configure_app as configure_app_  # noqa: PLC0415

    _app = FastAPI(title="RapidCull API")
    register_handlers(_app)
    _app.include_router(jobs_router_)
    configure_app_(_app)

    # In-memory collection registry — keyed by collection_id.
    # Stored on app.state so callers (tests, shell) can reach it via the app object.
    _collections: dict[str, Collection] = {}
    _app.state._collections = _collections

    @_app.post("/api/v1/collections/{collection_id}/query")
    def query_collection(collection_id: str, request: QueryRequest) -> dict[str, Any]:
        """Query a collection by parse expression; returns matching image IDs."""
        collection = _collections.get(collection_id)
        if collection is None:
            raise ApiError(
                code="COLLECTION_NOT_FOUND",
                message=f"Collection '{collection_id}' not found.",
                http_status=404,
            )

        parse_result = parse_query(request.query_text)
        if not parse_result.ok or parse_result.expression is None:
            error_messages = "; ".join(e.message for e in parse_result.errors)
            raise ApiError(
                code="QUERY_PARSE_ERROR",
                message=error_messages,
            )

        result = collection.query(parse_result.expression, query_text=request.query_text)
        return ok(
            {
                "matching_ids": result.matching_ids,
                "total_count": result.total_count,
                "query_expression": result.query_expression_text,
            }
        )

    if db_path is not None:
        _db_path = db_path

        @_app.on_event("startup")
        def _migrate_schema() -> None:
            before = get_schema_version(_db_path)
            try:
                create_or_validate_schema(_db_path)
            except SchemaVersionMismatchError:
                logger.error(
                    "Schema version mismatch: cannot auto-migrate DB at %s "
                    "(current on-disk=%s, target=%s). "
                    "Manual intervention required.",
                    _db_path,
                    before,
                    CURRENT_SCHEMA_VERSION,
                )
                raise
            after = get_schema_version(_db_path)
            if before != after:
                logger.info(
                    "Schema migrated: %s → %s (db=%s)",
                    before,
                    after,
                    _db_path,
                )
            else:
                logger.info(
                    "Schema up to date at version %s (db=%s)",
                    after,
                    _db_path,
                )

        from rapidcull import api_faces, api_search  # noqa: PLC0415

        # Configure and mount the new domain routers.
        api_images.configure_router(_db_path)
        api_galleries.configure_router(_db_path)
        api_persons.configure_router(_db_path, library_root=library_root)
        api_trash.configure_router(_db_path)
        api_faces.configure_router(_db_path)
        api_search.configure_router(_db_path)

        # search must be included before api_images so /api/v1/images/search
        # is not shadowed by the /api/v1/images/{image_id} path parameter route.
        _app.include_router(api_search.router)
        _app.include_router(api_images.router)
        _app.include_router(api_galleries.router)
        _app.include_router(api_persons.router)
        _app.include_router(api_trash.router)
        _app.include_router(api_faces.router)

        from rapidcull.api_jobs import configure_executor  # noqa: PLC0415
        from rapidcull.job_executor import JobExecutor  # noqa: PLC0415

        _executor = JobExecutor(db_path=_db_path, library_root=library_root)
        configure_executor(_executor)

        # Mount proxy/thumbnail static files.
        proxies_dir = _db_path.parent / "proxies"
        proxies_dir.mkdir(parents=True, exist_ok=True)
        _app.mount(
            "/proxies",
            StaticFiles(directory=str(proxies_dir), html=False),
            name="proxies",
        )

        # Mount frontend build output only if it exists.
        frontend_dist = Path(__file__).parent.parent.parent / "frontend" / "dist"
        if frontend_dist.exists():
            _app.mount(
                "/",
                StaticFiles(directory=str(frontend_dist), html=True),
                name="frontend",
            )

    return _app


def _make_app() -> FastAPI:
    import os  # noqa: PLC0415

    db_env = os.environ.get("RAPIDCULL_DB_PATH")
    lib_env = os.environ.get("RAPIDCULL_LIBRARY_ROOT")
    return create_app(
        db_path=Path(db_env) if db_env else None,
        library_root=Path(lib_env) if lib_env else None,
    )


app = _make_app()
# Expose the collection registry at module level so tests and tooling can seed it.
_collections: dict[str, Collection] = app.state._collections
