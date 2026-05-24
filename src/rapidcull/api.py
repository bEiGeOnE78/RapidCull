from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from rapidcull.collections import Collection
from rapidcull.query_grammar import parse_query

app = FastAPI(title="RapidCull API")

# In-memory collection registry — keyed by collection_id.
_collections: dict[str, Collection] = {}


class QueryRequest(BaseModel):
    query_text: str


class QueryResponse(BaseModel):
    matching_ids: list[str]
    total_count: int
    query_expression: str


@app.post(
    "/api/v1/collections/{collection_id}/query",
    response_model=QueryResponse,
)
def query_collection(collection_id: str, request: QueryRequest) -> QueryResponse:
    """Query a collection by parse expression; returns matching image IDs."""
    collection = _collections.get(collection_id)
    if collection is None:
        raise HTTPException(status_code=404, detail=f"Collection '{collection_id}' not found.")

    parse_result = parse_query(request.query_text)
    if not parse_result.ok or parse_result.expression is None:
        error_messages = "; ".join(e.message for e in parse_result.errors)
        raise HTTPException(status_code=400, detail=error_messages)

    result = collection.query(parse_result.expression, query_text=request.query_text)
    return QueryResponse(
        matching_ids=result.matching_ids,
        total_count=result.total_count,
        query_expression=result.query_expression_text,
    )
