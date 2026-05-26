from __future__ import annotations

from typing import Any

from fastapi import FastAPI
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
