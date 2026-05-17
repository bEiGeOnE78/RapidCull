from __future__ import annotations

import re
from pathlib import Path

import pytest

from rapidcull.query_grammar import parse_query

DOC_PATH = (
    Path(__file__).resolve().parents[3]
    / "docs/20260328T223918--query-grammar-v1-behavior__projects.md"
)
VALID_EXAMPLE_PATTERN = re.compile(r"^- `(?P<query>.+)` -> ok$", re.MULTILINE)
INVALID_EXAMPLE_PATTERN = re.compile(
    r"^- `(?P<query>.+)` -> error:(?P<code>[a-z_]+)$",
    re.MULTILINE,
)


@pytest.mark.fr
@pytest.mark.integration
def test_fr_022_query_behavior_doc_exists_with_required_sections() -> None:
    assert DOC_PATH.is_file(), f"Expected query behavior doc at {DOC_PATH}"

    document = DOC_PATH.read_text(encoding="utf-8")

    assert "# Query Grammar v1 Behavior" in document
    assert "## Supported Fields" in document
    assert "## Supported Operators" in document
    assert "## Boolean Logic" in document
    assert "## Valid Examples" in document
    assert "## Invalid Examples" in document


@pytest.mark.fr
@pytest.mark.integration
def test_fr_022_documented_query_examples_match_current_parser_contract() -> None:
    assert DOC_PATH.is_file(), f"Expected query behavior doc at {DOC_PATH}"

    document = DOC_PATH.read_text(encoding="utf-8")
    valid_examples = VALID_EXAMPLE_PATTERN.findall(document)
    invalid_examples = INVALID_EXAMPLE_PATTERN.findall(document)

    assert valid_examples, "Expected at least one documented valid query example"
    assert invalid_examples, "Expected at least one documented invalid query example"

    for query in valid_examples:
        result = parse_query(query)
        assert result.ok, f"Expected documented valid query to parse: {query}"

    for query, error_code in invalid_examples:
        result = parse_query(query)
        assert not result.ok, f"Expected documented invalid query to fail: {query}"
        assert result.errors[0].code == error_code


@pytest.mark.fr
@pytest.mark.integration
def test_fr_022_query_behavior_doc_covers_additional_valid_contract_examples() -> None:
    assert DOC_PATH.is_file(), f"Expected query behavior doc at {DOC_PATH}"

    document = DOC_PATH.read_text(encoding="utf-8")

    assert "- `date>=2024-01-01` -> ok" in document
    assert "- `keyword~portrait` -> ok" in document
    assert "- `fnumber<=2.8` -> ok" in document


@pytest.mark.fr
@pytest.mark.integration
def test_fr_022_query_behavior_doc_covers_additional_invalid_contract_examples() -> None:
    assert DOC_PATH.is_file(), f"Expected query behavior doc at {DOC_PATH}"

    document = DOC_PATH.read_text(encoding="utf-8")

    assert "- `iso>=fast` -> error:invalid_number" in document
    assert "- `person=alice AND` -> error:missing_expression" in document
    assert "- `person=alice AND OR person=bob` -> error:invalid_boolean_pair" in document


@pytest.mark.fr
@pytest.mark.integration
def test_fr_022_query_behavior_doc_covers_final_invalid_contract_examples() -> None:
    assert DOC_PATH.is_file(), f"Expected query behavior doc at {DOC_PATH}"

    document = DOC_PATH.read_text(encoding="utf-8")

    assert "- `person=` -> error:missing_value" in document
    assert "- `(` -> error:missing_group_expression" in document
    assert "- `person=alice)` -> error:unexpected_closing_parenthesis" in document
    assert "- `person==alice` -> error:invalid_operator" in document
