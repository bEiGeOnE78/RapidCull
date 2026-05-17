from __future__ import annotations

import pytest

from rapidcull.query_evaluator import evaluate_query
from rapidcull.query_grammar import QueryBinary, QueryComparison, QueryNot


@pytest.mark.fr
@pytest.mark.integration
def test_query_evaluator_matches_any_value_in_multi_value_person_field() -> None:
    record = {
        "person": ["alice", "bob"],
        "date": "2024-01-15",
        "camera": "Leica Q2",
        "iso": 800,
        "fnumber": 2.8,
        "keyword": ["Portrait", "Studio Light"],
    }

    result = evaluate_query(
        QueryComparison(field="person", operator="=", value="bob"),
        record,
    )

    assert result is True


@pytest.mark.fr
@pytest.mark.integration
def test_query_evaluator_uses_case_insensitive_text_matching_for_multi_value_fields() -> None:
    record = {
        "person": ["alice", "bob"],
        "keyword": ["Portrait", "Studio Light"],
    }

    result = evaluate_query(
        QueryComparison(field="keyword", operator="~", value="studio"),
        record,
    )

    assert result is True


@pytest.mark.fr
@pytest.mark.integration
def test_query_evaluator_requires_present_field_for_text_inequality_match() -> None:
    record = {
        "camera": "Leica Q2",
    }

    result = evaluate_query(
        QueryComparison(field="keyword", operator="!=", value="blurred"),
        record,
    )

    assert result is False


@pytest.mark.fr
@pytest.mark.integration
def test_query_evaluator_treats_empty_multi_value_text_field_as_non_match() -> None:
    record = {
        "camera": "Nikon Zf",
        "person": [],
        "keyword": [],
    }

    result = evaluate_query(
        QueryComparison(field="keyword", operator="!=", value="portrait"),
        record,
    )

    assert result is False


@pytest.mark.fr
@pytest.mark.integration
def test_query_evaluator_applies_ordered_numeric_and_date_comparisons() -> None:
    record = {
        "date": "2024-01-15",
        "iso": 800,
        "fnumber": 2.8,
        "focal": 50.0,
    }

    result = evaluate_query(
        QueryBinary(
            operator="AND",
            left=QueryComparison(field="date", operator=">=", value="2024-01-01"),
            right=QueryComparison(field="iso", operator=">", value="400"),
        ),
        record,
    )

    assert result is True


@pytest.mark.fr
@pytest.mark.integration
def test_query_evaluator_honors_boolean_composition_for_canonical_contract_example() -> None:
    record = {
        "person": ["alice", "bob"],
        "date": "2024-01-15",
        "camera": "Leica Q2",
        "iso": 800,
        "fnumber": 2.8,
        "keyword": ["Portrait", "Studio Light"],
    }

    result = evaluate_query(
        QueryBinary(
            operator="AND",
            left=QueryBinary(
                operator="OR",
                left=QueryComparison(field="person", operator="=", value="alice"),
                right=QueryComparison(field="person", operator="=", value="bob"),
            ),
            right=QueryNot(operand=QueryComparison(field="keyword", operator="=", value="blurred")),
        ),
        record,
    )

    assert result is True
