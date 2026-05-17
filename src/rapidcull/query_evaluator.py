from __future__ import annotations

from collections.abc import Mapping
from typing import TypeAlias

from rapidcull.query_grammar import (
    INTEGER_FIELDS,
    NUMBER_FIELDS,
    QueryBinary,
    QueryComparison,
    QueryExpression,
    QueryNot,
)

QueryRecordValue: TypeAlias = str | int | float | bool | None | list[str]
QueryRecord: TypeAlias = Mapping[str, QueryRecordValue]

MULTI_VALUE_TEXT_FIELDS = frozenset({"person", "keyword"})
SINGLE_VALUE_TEXT_FIELDS = frozenset({"camera", "lens"})


def evaluate_query(expression: QueryExpression, record: QueryRecord) -> bool:
    if isinstance(expression, QueryComparison):
        return _evaluate_comparison(expression, record)
    if isinstance(expression, QueryBinary):
        return _evaluate_binary(expression, record)
    if isinstance(expression, QueryNot):
        return not evaluate_query(expression.operand, record)
    raise ValueError(f"Unsupported query expression: {type(expression)!r}")


def _evaluate_binary(expression: QueryBinary, record: QueryRecord) -> bool:
    if expression.operator == "AND":
        return evaluate_query(expression.left, record) and evaluate_query(expression.right, record)
    if expression.operator == "OR":
        return evaluate_query(expression.left, record) or evaluate_query(expression.right, record)
    raise ValueError(f"Unsupported boolean operator: {expression.operator}")


def _evaluate_comparison(expression: QueryComparison, record: QueryRecord) -> bool:
    value = record.get(expression.field)
    if expression.field in MULTI_VALUE_TEXT_FIELDS | SINGLE_VALUE_TEXT_FIELDS:
        return _evaluate_text_comparison(expression.operator, expression.value, value)
    if expression.field == "date":
        return _evaluate_date_comparison(expression.operator, expression.value, value)
    if expression.field in INTEGER_FIELDS:
        return _evaluate_numeric_comparison(
            expression.operator, int(expression.value), _as_int(value)
        )
    if expression.field in NUMBER_FIELDS:
        return _evaluate_numeric_comparison(
            expression.operator,
            float(expression.value),
            _as_number(value),
        )
    raise ValueError(f"Unsupported field: {expression.field}")


def _evaluate_text_comparison(
    operator: str, query_value: str, value: QueryRecordValue | None
) -> bool:
    candidates = _normalize_text_candidates(value)
    if not candidates:
        return False

    normalized_query = query_value.casefold()
    if operator == "=":
        return any(candidate == normalized_query for candidate in candidates)
    if operator == "!=":
        return all(candidate != normalized_query for candidate in candidates)
    if operator == "~":
        return any(normalized_query in candidate for candidate in candidates)
    raise ValueError(f"Unsupported text operator: {operator}")


def _normalize_text_candidates(value: QueryRecordValue | None) -> list[str]:
    if isinstance(value, str):
        return [value.casefold()] if value else []
    if isinstance(value, list):
        return [candidate.casefold() for candidate in value if candidate]
    return []


def _evaluate_date_comparison(
    operator: str, query_value: str, value: QueryRecordValue | None
) -> bool:
    if not isinstance(value, str) or not value:
        return False
    return _compare_ordered_text(operator, value, query_value)


def _evaluate_numeric_comparison(
    operator: str,
    query_value: int | float,
    record_value: int | float | None,
) -> bool:
    if record_value is None:
        return False
    return _compare_ordered_number(operator, record_value, query_value)


def _compare_ordered_text(operator: str, left: str, right: str) -> bool:
    if operator == "=":
        return left == right
    if operator == "!=":
        return left != right
    if operator == ">":
        return left > right
    if operator == ">=":
        return left >= right
    if operator == "<":
        return left < right
    if operator == "<=":
        return left <= right
    raise ValueError(f"Unsupported ordered operator: {operator}")


def _compare_ordered_number(operator: str, left: int | float, right: int | float) -> bool:
    if operator == "=":
        return left == right
    if operator == "!=":
        return left != right
    if operator == ">":
        return left > right
    if operator == ">=":
        return left >= right
    if operator == "<":
        return left < right
    if operator == "<=":
        return left <= right
    raise ValueError(f"Unsupported ordered operator: {operator}")


def _as_int(value: QueryRecordValue | None) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    return value


def _as_number(value: QueryRecordValue | None) -> float | None:
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    return float(value)
