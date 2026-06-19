from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from rapidcull.api_envelope import ApiError, ok, register_handlers
from rapidcull.api_jobs import router as jobs_router
from rapidcull.collections import Collection
from rapidcull.query_grammar import parse_query
from rapidcull.security import configure_app

app = FastAPI(title="RapidCull API")

# Register standard response-envelope exception handlers.
register_handlers(app)

# Mount job-orchestration endpoints.
app.include_router(jobs_router)

# Configure CORS and auth middleware from environment settings.
configure_app(app)

# In-memory collection registry — keyed by collection_id.
_collections: dict[str, Collection] = {}


class QueryRequest(BaseModel):
    query_text: str


@app.post("/api/v1/collections/{collection_id}/query")
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


def create_app(db_path: Path | None = None, library_root: Path | None = None) -> FastAPI:
    """Create a FastAPI application instance with optional DB path for face endpoints."""
    from rapidcull import api_galleries, api_images, api_persons, api_trash  # noqa: PLC0415
    from rapidcull.api_envelope import register_handlers  # noqa: PLC0415
    from rapidcull.api_jobs import router as jobs_router_  # noqa: PLC0415
    from rapidcull.security import configure_app as configure_app_  # noqa: PLC0415

    _app = FastAPI(title="RapidCull API")
    register_handlers(_app)
    _app.include_router(jobs_router_)
    configure_app_(_app)

    if db_path is not None:
        _db_path = db_path

        # Configure and mount the new domain routers.
        api_images.configure_router(_db_path)
        api_galleries.configure_router(_db_path)
        api_persons.configure_router(_db_path)
        api_trash.configure_router(_db_path)

        _app.include_router(api_images.router)
        _app.include_router(api_galleries.router)
        _app.include_router(api_persons.router)
        _app.include_router(api_trash.router)

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
