from __future__ import annotations

import pytest

from rapidcull.query_grammar import (
    QueryBinary,
    QueryComparison,
    QueryNot,
    QueryParseResult,
    QueryValidationError,
    parse_query,
)


@pytest.mark.fr
@pytest.mark.integration
def test_fr_017_parses_valid_grammar_query_into_typed_expression_tree() -> None:
    result = parse_query("person=alice")

    assert result == QueryParseResult(
        ok=True,
        expression=QueryComparison(field="person", operator="=", value="alice"),
        errors=[],
    )


@pytest.mark.fr
@pytest.mark.integration
def test_fr_020_honors_boolean_parentheses_and_not_precedence() -> None:
    result = parse_query("(person=alice OR person=bob) AND NOT keyword=blurred")

    assert result == QueryParseResult(
        ok=True,
        expression=QueryBinary(
            operator="AND",
            left=QueryBinary(
                operator="OR",
                left=QueryComparison(field="person", operator="=", value="alice"),
                right=QueryComparison(field="person", operator="=", value="bob"),
            ),
            right=QueryNot(operand=QueryComparison(field="keyword", operator="=", value="blurred")),
        ),
        errors=[],
    )


@pytest.mark.fr
@pytest.mark.integration
def test_fr_018_rejects_unknown_field_with_actionable_suggestion() -> None:
    result = parse_query("people=alice")

    assert result == QueryParseResult(
        ok=False,
        expression=None,
        errors=[
            QueryValidationError(
                code="unknown_field",
                message="Unknown field 'people'. Did you mean 'person'?",
                token="people",
                suggestions=["person"],
            )
        ],
    )


@pytest.mark.fr
@pytest.mark.integration
def test_fr_019_rejects_operator_not_supported_for_field_type() -> None:
    result = parse_query("person>alice")

    assert result == QueryParseResult(
        ok=False,
        expression=None,
        errors=[
            QueryValidationError(
                code="unsupported_operator",
                message=(
                    "Operator '>' is not supported for field 'person'. "
                    "Allowed operators: =, !=, ~."
                ),
                token=">",
                suggestions=["=", "!=", "~"],
            )
        ],
    )


@pytest.mark.fr
@pytest.mark.integration
def test_fr_021_rejects_bad_date_with_expected_format_message() -> None:
    result = parse_query("date>=2024/01/01")

    assert result == QueryParseResult(
        ok=False,
        expression=None,
        errors=[
            QueryValidationError(
                code="invalid_date",
                message="Invalid date value '2024/01/01'. Expected format: YYYY-MM-DD.",
                token="2024/01/01",
                suggestions=["YYYY-MM-DD"],
            )
        ],
    )


@pytest.mark.fr
@pytest.mark.integration
def test_fr_021_rejects_mismatched_parentheses_with_actionable_error() -> None:
    result = parse_query("(person=alice OR person=bob")

    assert result == QueryParseResult(
        ok=False,
        expression=None,
        errors=[
            QueryValidationError(
                code="mismatched_parentheses",
                message="Missing closing ')' for grouped expression.",
                token=")",
                suggestions=[")"],
            )
        ],
    )


@pytest.mark.fr
@pytest.mark.integration
def test_fr_019_rejects_non_integer_iso_value_with_expected_format_message() -> None:
    result = parse_query("iso>=fast")

    assert result == QueryParseResult(
        ok=False,
        expression=None,
        errors=[
            QueryValidationError(
                code="invalid_number",
                message="Invalid numeric value 'fast' for field 'iso'. Expected an integer.",
                token="fast",
                suggestions=["integer"],
            )
        ],
    )


@pytest.mark.fr
@pytest.mark.integration
def test_fr_019_rejects_non_numeric_fnumber_value_with_expected_format_message() -> None:
    result = parse_query("fnumber<=wide")

    assert result == QueryParseResult(
        ok=False,
        expression=None,
        errors=[
            QueryValidationError(
                code="invalid_number",
                message="Invalid numeric value 'wide' for field 'fnumber'. Expected a number.",
                token="wide",
                suggestions=["number"],
            )
        ],
    )


@pytest.mark.fr
@pytest.mark.integration
def test_fr_021_rejects_unterminated_bang_token_with_actionable_error() -> None:
    result = parse_query("person!alice")

    assert result == QueryParseResult(
        ok=False,
        expression=None,
        errors=[
            QueryValidationError(
                code="invalid_token",
                message="Unexpected token '!'. Expected operator '!='.",
                token="!",
                suggestions=["!="],
            )
        ],
    )


@pytest.mark.fr
@pytest.mark.integration
def test_fr_021_rejects_missing_value_after_operator_with_expected_guidance() -> None:
    result = parse_query("person=")

    assert result == QueryParseResult(
        ok=False,
        expression=None,
        errors=[
            QueryValidationError(
                code="missing_value",
                message="Expected value after operator '='.",
                token="",
                suggestions=["<value>"],
            )
        ],
    )


@pytest.mark.fr
@pytest.mark.integration
def test_fr_021_rejects_trailing_boolean_operator_with_expected_expression_guidance() -> None:
    result = parse_query("person=alice AND")

    assert result == QueryParseResult(
        ok=False,
        expression=None,
        errors=[
            QueryValidationError(
                code="missing_expression",
                message="Expected expression after boolean operator 'AND'.",
                token="AND",
                suggestions=["<field><operator><value>", "("],
            )
        ],
    )


@pytest.mark.fr
@pytest.mark.integration
def test_fr_021_rejects_grouped_trailing_and_with_missing_expression_error() -> None:
    result = parse_query("(person=alice AND)")

    assert result == QueryParseResult(
        ok=False,
        expression=None,
        errors=[
            QueryValidationError(
                code="missing_expression",
                message="Expected expression after boolean operator 'AND'.",
                token="AND",
                suggestions=["<field><operator><value>", "("],
            )
        ],
    )


@pytest.mark.fr
@pytest.mark.integration
def test_fr_021_rejects_grouped_trailing_or_with_missing_expression_error() -> None:
    result = parse_query("(person=alice OR)")

    assert result == QueryParseResult(
        ok=False,
        expression=None,
        errors=[
            QueryValidationError(
                code="missing_expression",
                message="Expected expression after boolean operator 'OR'.",
                token="OR",
                suggestions=["<field><operator><value>", "("],
            )
        ],
    )


@pytest.mark.fr
@pytest.mark.integration
def test_fr_021_rejects_empty_grouped_expression_with_actionable_error() -> None:
    result = parse_query("()")

    assert result == QueryParseResult(
        ok=False,
        expression=None,
        errors=[
            QueryValidationError(
                code="empty_group",
                message="Grouped expression cannot be empty.",
                token="()",
                suggestions=["<field><operator><value>", "NOT", "("],
            )
        ],
    )


@pytest.mark.fr
@pytest.mark.integration
def test_fr_021_rejects_not_followed_by_closing_parenthesis_with_actionable_error() -> None:
    result = parse_query("NOT)")

    assert result == QueryParseResult(
        ok=False,
        expression=None,
        errors=[
            QueryValidationError(
                code="missing_expression",
                message="Expected expression after boolean operator 'NOT'.",
                token="NOT",
                suggestions=["<field><operator><value>", "("],
            )
        ],
    )


@pytest.mark.fr
@pytest.mark.integration
def test_fr_021_rejects_not_space_closing_parenthesis_with_actionable_error() -> None:
    result = parse_query("NOT )")

    assert result == QueryParseResult(
        ok=False,
        expression=None,
        errors=[
            QueryValidationError(
                code="missing_expression",
                message="Expected expression after boolean operator 'NOT'.",
                token="NOT",
                suggestions=["<field><operator><value>", "("],
            )
        ],
    )


@pytest.mark.fr
@pytest.mark.integration
def test_fr_021_rejects_group_starting_with_and_with_actionable_error() -> None:
    result = parse_query("(AND person=alice)")

    assert result == QueryParseResult(
        ok=False,
        expression=None,
        errors=[
            QueryValidationError(
                code="invalid_group_start",
                message="Boolean operator 'AND' cannot start a grouped expression.",
                token="AND",
                suggestions=["NOT", "<field><operator><value>", "("],
            )
        ],
    )


@pytest.mark.fr
@pytest.mark.integration
def test_fr_021_rejects_group_starting_with_or_with_actionable_error() -> None:
    result = parse_query("(OR person=alice)")

    assert result == QueryParseResult(
        ok=False,
        expression=None,
        errors=[
            QueryValidationError(
                code="invalid_group_start",
                message="Boolean operator 'OR' cannot start a grouped expression.",
                token="OR",
                suggestions=["NOT", "<field><operator><value>", "("],
            )
        ],
    )


@pytest.mark.fr
@pytest.mark.integration
def test_fr_021_rejects_open_group_at_eof_with_actionable_error() -> None:
    result = parse_query("(")

    assert result == QueryParseResult(
        ok=False,
        expression=None,
        errors=[
            QueryValidationError(
                code="missing_group_expression",
                message="Expected expression after '('.",
                token="(",
                suggestions=["NOT", "<field><operator><value>", "("],
            )
        ],
    )


@pytest.mark.fr
@pytest.mark.integration
def test_fr_021_rejects_not_open_group_at_eof_with_actionable_error() -> None:
    result = parse_query("NOT(")

    assert result == QueryParseResult(
        ok=False,
        expression=None,
        errors=[
            QueryValidationError(
                code="missing_group_expression",
                message="Expected expression after '('.",
                token="(",
                suggestions=["NOT", "<field><operator><value>", "("],
            )
        ],
    )


@pytest.mark.fr
@pytest.mark.integration
def test_fr_021_rejects_and_followed_by_or_with_actionable_error() -> None:
    result = parse_query("person=alice AND OR person=bob")

    assert result == QueryParseResult(
        ok=False,
        expression=None,
        errors=[
            QueryValidationError(
                code="invalid_boolean_pair",
                message="Boolean operator 'OR' cannot follow 'AND'.",
                token="OR",
                suggestions=["NOT", "<field><operator><value>", "("],
            )
        ],
    )


@pytest.mark.fr
@pytest.mark.integration
def test_fr_021_rejects_or_followed_by_and_with_actionable_error() -> None:
    result = parse_query("person=alice OR AND person=bob")

    assert result == QueryParseResult(
        ok=False,
        expression=None,
        errors=[
            QueryValidationError(
                code="invalid_boolean_pair",
                message="Boolean operator 'AND' cannot follow 'OR'.",
                token="AND",
                suggestions=["NOT", "<field><operator><value>", "("],
            )
        ],
    )


@pytest.mark.fr
@pytest.mark.integration
def test_fr_021_rejects_leading_boolean_operator_with_actionable_error() -> None:
    result = parse_query("AND person=alice")

    assert result == QueryParseResult(
        ok=False,
        expression=None,
        errors=[
            QueryValidationError(
                code="invalid_boolean_position",
                message="Boolean operator 'AND' cannot start an expression.",
                token="AND",
                suggestions=["NOT", "(", "<field><operator><value>"],
            )
        ],
    )


@pytest.mark.fr
@pytest.mark.integration
def test_fr_021_rejects_unmatched_closing_parenthesis_with_actionable_error() -> None:
    result = parse_query("person=alice)")

    assert result == QueryParseResult(
        ok=False,
        expression=None,
        errors=[
            QueryValidationError(
                code="unexpected_closing_parenthesis",
                message="Unexpected closing ')' with no matching opening '('.",
                token=")",
                suggestions=["remove ')'"],
            )
        ],
    )


@pytest.mark.fr
@pytest.mark.integration
def test_fr_021_rejects_double_equals_operator_with_expected_guidance() -> None:
    result = parse_query("person==alice")

    assert result == QueryParseResult(
        ok=False,
        expression=None,
        errors=[
            QueryValidationError(
                code="invalid_operator",
                message="Unexpected operator '=' after '='. Use a single '=' for equality.",
                token="=",
                suggestions=["="],
            )
        ],
    )


@pytest.mark.fr
@pytest.mark.integration
def test_fr_021_rejects_double_gt_operator_with_expected_guidance() -> None:
    result = parse_query("iso>>100")

    assert result == QueryParseResult(
        ok=False,
        expression=None,
        errors=[
            QueryValidationError(
                code="invalid_operator",
                message="Unexpected operator '>' after '>'. Use a single '>' or '>='.",
                token=">",
                suggestions=[">", ">="],
            )
        ],
    )
