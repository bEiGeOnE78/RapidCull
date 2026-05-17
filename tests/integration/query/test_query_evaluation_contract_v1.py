from __future__ import annotations

from pathlib import Path

import pytest

DOC_PATH = (
    Path(__file__).resolve().parents[3]
    / "docs/20260329T080544--query-evaluation-contract-v1__projects.md"
)


@pytest.mark.fr
@pytest.mark.integration
def test_query_evaluation_contract_v1_doc_exists_with_required_sections() -> None:
    assert DOC_PATH.is_file(), f"Expected query evaluation contract doc at {DOC_PATH}"

    document = DOC_PATH.read_text(encoding="utf-8")

    assert "# Query Evaluation Contract v1" in document
    assert "## Scope" in document
    assert "## Evaluator Input Contract" in document
    assert "## Comparison Semantics" in document
    assert "## Boolean Semantics" in document
    assert "## Missing Metadata Policy" in document
    assert "## Evaluator Output Contract" in document
    assert "## Canonical Evaluation Examples" in document


@pytest.mark.fr
@pytest.mark.integration
def test_query_evaluation_contract_v1_doc_covers_required_semantic_points() -> None:
    assert DOC_PATH.is_file(), f"Expected query evaluation contract doc at {DOC_PATH}"

    document = DOC_PATH.read_text(encoding="utf-8")

    assert "text equality (`=`)" in document
    assert "text inequality (`!=`)" in document
    assert "contains (`~`)" in document
    assert "ordered comparisons (`>`, `>=`, `<`, `<=`)" in document
    assert "missing fields evaluate as non-matches" in document
    assert "`AND` requires both operands to match" in document
    assert "`OR` requires at least one operand to match" in document
    assert "`NOT` negates the operand result" in document


@pytest.mark.fr
@pytest.mark.integration
def test_query_evaluation_contract_v1_doc_clarifies_text_matching_rules() -> None:
    assert DOC_PATH.is_file(), f"Expected query evaluation contract doc at {DOC_PATH}"

    document = DOC_PATH.read_text(encoding="utf-8")
    inequality_rule = (
        "`!=` matches when the field is present and no normalized "
        "field value equals the query value"
    )
    contains_rule = (
        "`~` matches when the query value is a case-insensitive substring "
        "of any normalized field value"
    )

    assert "text comparisons are case-insensitive" in document
    assert "`person` and `keyword` are evaluated as multi-value text fields" in document
    assert "`=` matches when any normalized field value exactly equals the query value" in document
    assert inequality_rule in document
    assert contains_rule in document
    assert (
        "empty text fields behave like fields with no candidate values and evaluate as non-matches"
        in document
    )


@pytest.mark.fr
@pytest.mark.integration
def test_query_evaluation_contract_v1_doc_includes_canonical_record_examples() -> None:
    assert DOC_PATH.is_file(), f"Expected query evaluation contract doc at {DOC_PATH}"

    document = DOC_PATH.read_text(encoding="utf-8")

    assert "Record A" in document
    assert "person=alice" in document
    assert "keyword~portrait" in document
    assert "(person=alice OR person=bob) AND NOT keyword=blurred" in document
    assert "match" in document
    assert "non-match" in document


@pytest.mark.fr
@pytest.mark.integration
def test_query_evaluation_contract_v1_doc_has_multi_value_matching_examples() -> None:
    assert DOC_PATH.is_file(), f"Expected query evaluation contract doc at {DOC_PATH}"

    document = DOC_PATH.read_text(encoding="utf-8")

    assert '"person": ["alice", "bob"]' in document
    assert "person=bob` -> match" in document
    assert '"keyword": ["Portrait", "Studio Light"]' in document
    assert "person=ALICE` -> match" in document
    assert "keyword~studio` -> match" in document
    assert "keyword!=blurred` -> match" in document
