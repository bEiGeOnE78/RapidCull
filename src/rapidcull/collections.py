from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from rapidcull.query_evaluator import QueryRecord, evaluate_query
from rapidcull.query_grammar import QueryExpression


@dataclass(frozen=True)
class QueryResult:
    matching_ids: list[str]
    total_count: int
    query_expression_text: str


@dataclass
class Collection:
    collection_id: str
    name: str
    image_ids: list[str]
    metadata_index: dict[str, QueryRecord]

    def query(self, expression: QueryExpression, query_text: str = "") -> QueryResult:
        """Apply query expression to collection, return matching image IDs."""
        matching_ids = []
        for image_id in self.image_ids:
            record = self.metadata_index.get(image_id)
            if record and evaluate_query(expression, record):
                matching_ids.append(image_id)
        return QueryResult(
            matching_ids=matching_ids,
            total_count=len(self.image_ids),
            query_expression_text=query_text,
        )

    @classmethod
    def from_metadata(
        cls, collection_id: str, name: str, metadata_dict: dict[str, QueryRecord]
    ) -> Collection:
        """Create collection from metadata dict."""
        return cls(
            collection_id=collection_id,
            name=name,
            image_ids=list(metadata_dict.keys()),
            metadata_index=metadata_dict,
        )
