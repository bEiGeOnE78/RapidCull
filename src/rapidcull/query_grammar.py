from __future__ import annotations

import re
from dataclasses import dataclass
from difflib import get_close_matches
from typing import TypeAlias

SUPPORTED_FIELDS = (
    "person",
    "date",
    "camera",
    "lens",
    "iso",
    "fnumber",
    "focal",
    "keyword",
)
TEXT_OPERATORS = ("=", "!=", "~")
ORDERED_OPERATORS = ("=", "!=", ">", ">=", "<", "<=")
ALLOWED_OPERATORS_BY_FIELD = {
    "person": TEXT_OPERATORS,
    "date": ORDERED_OPERATORS,
    "camera": TEXT_OPERATORS,
    "lens": TEXT_OPERATORS,
    "iso": ORDERED_OPERATORS,
    "fnumber": ORDERED_OPERATORS,
    "focal": ORDERED_OPERATORS,
    "keyword": TEXT_OPERATORS,
}
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
INTEGER_FIELDS = {"iso"}
NUMBER_FIELDS = {"fnumber", "focal"}


@dataclass(frozen=True)
class QueryComparison:
    field: str
    operator: str
    value: str


QueryExpression: TypeAlias = "QueryComparison | QueryBinary | QueryNot"


@dataclass(frozen=True)
class QueryBinary:
    operator: str
    left: QueryExpression
    right: QueryExpression


@dataclass(frozen=True)
class QueryNot:
    operand: QueryExpression


@dataclass(frozen=True)
class QueryValidationError:
    code: str
    message: str
    token: str
    suggestions: list[str]


@dataclass(frozen=True)
class QueryParseResult:
    ok: bool
    expression: QueryExpression | None
    errors: list[QueryValidationError]


@dataclass(frozen=True)
class _Token:
    kind: str
    value: str


class _Parser:
    def __init__(self, tokens: list[_Token]) -> None:
        self._tokens = tokens
        self._index = 0
        self.error: QueryValidationError | None = None

    def parse(self) -> QueryExpression | None:
        expression = self._parse_or_expression()
        if self.error is not None:
            return None
        if self._current().kind != "EOF":
            if self._current().kind == "RPAREN":
                self.error = QueryValidationError(
                    code="unexpected_closing_parenthesis",
                    message="Unexpected closing ')' with no matching opening '('.",
                    token=")",
                    suggestions=["remove ')'"],
                )
                return None
            self.error = QueryValidationError(
                code="invalid_token",
                message=f"Unexpected token '{self._current().value}'.",
                token=self._current().value,
                suggestions=[],
            )
            return None
        return expression

    def _parse_or_expression(self) -> QueryExpression | None:
        left = self._parse_and_expression()
        while left is not None and self._match_keyword("OR"):
            if self._current().kind in {"EOF", "RPAREN"}:
                self.error = _missing_expression_after_boolean_error("OR")
                return None
            if self._current().kind == "ATOM" and self._current().value.upper() in {"AND", "OR"}:
                self.error = _invalid_boolean_pair_error("OR", self._current().value.upper())
                return None
            right = self._parse_and_expression()
            if right is None:
                return None
            left = QueryBinary(operator="OR", left=left, right=right)
        return left

    def _parse_and_expression(self) -> QueryExpression | None:
        left = self._parse_not_expression()
        while left is not None and self._match_keyword("AND"):
            if self._current().kind in {"EOF", "RPAREN"}:
                self.error = _missing_expression_after_boolean_error("AND")
                return None
            if self._current().kind == "ATOM" and self._current().value.upper() in {"AND", "OR"}:
                self.error = _invalid_boolean_pair_error("AND", self._current().value.upper())
                return None
            right = self._parse_not_expression()
            if right is None:
                return None
            left = QueryBinary(operator="AND", left=left, right=right)
        return left

    def _parse_not_expression(self) -> QueryExpression | None:
        if self._match_keyword("NOT"):
            if self._current().kind in {"EOF", "RPAREN"}:
                self.error = _missing_expression_after_boolean_error("NOT")
                return None
            operand = self._parse_not_expression()
            if operand is None:
                return None
            return QueryNot(operand=operand)
        return self._parse_primary()

    def _parse_primary(self) -> QueryExpression | None:
        if self._match_kind("LPAREN"):
            if self._current().kind == "EOF":
                self.error = QueryValidationError(
                    code="missing_group_expression",
                    message="Expected expression after '('.",
                    token="(",
                    suggestions=["NOT", "<field><operator><value>", "("],
                )
                return None
            if self._current().kind == "RPAREN":
                self.error = QueryValidationError(
                    code="empty_group",
                    message="Grouped expression cannot be empty.",
                    token="()",
                    suggestions=["<field><operator><value>", "NOT", "("],
                )
                return None
            if self._current().kind == "ATOM" and self._current().value.upper() in {"AND", "OR"}:
                operator = self._current().value.upper()
                self.error = QueryValidationError(
                    code="invalid_group_start",
                    message=f"Boolean operator '{operator}' cannot start a grouped expression.",
                    token=operator,
                    suggestions=["NOT", "<field><operator><value>", "("],
                )
                return None
            expression = self._parse_or_expression()
            if expression is None:
                return None
            if not self._match_kind("RPAREN"):
                self.error = QueryValidationError(
                    code="mismatched_parentheses",
                    message="Missing closing ')' for grouped expression.",
                    token=")",
                    suggestions=[")"],
                )
                return None
            return expression
        if self._current().kind == "ATOM" and self._current().value.upper() in {"AND", "OR"}:
            operator = self._current().value.upper()
            self.error = QueryValidationError(
                code="invalid_boolean_position",
                message=f"Boolean operator '{operator}' cannot start an expression.",
                token=operator,
                suggestions=["NOT", "(", "<field><operator><value>"],
            )
            return None
        return self._parse_comparison()

    def _parse_comparison(self) -> QueryExpression | None:
        field_token = self._current()
        if field_token.kind != "ATOM":
            self.error = self._unexpected_token_error(field_token)
            return None
        self._advance()

        operator_token = self._current()
        if operator_token.kind != "OP":
            if operator_token.kind == "INVALID" and operator_token.value == "!":
                self.error = QueryValidationError(
                    code="invalid_token",
                    message="Unexpected token '!'. Expected operator '!='.",
                    token="!",
                    suggestions=["!="],
                )
                return None
            self.error = QueryValidationError(
                code="invalid_syntax",
                message=f"Expected operator after field '{field_token.value}'.",
                token=operator_token.value,
                suggestions=list(TEXT_OPERATORS),
            )
            return None
        self._advance()

        value_token = self._current()
        if value_token.kind == "OP":
            self.error = _double_operator_error(
                first_operator=operator_token.value,
                second_operator=value_token.value,
            )
            return None
        if value_token.kind != "ATOM":
            self.error = QueryValidationError(
                code="missing_value",
                message=f"Expected value after operator '{operator_token.value}'.",
                token=value_token.value,
                suggestions=["<value>"],
            )
            return None
        self._advance()

        return QueryComparison(
            field=field_token.value.lower(),
            operator=operator_token.value,
            value=value_token.value,
        )

    def _current(self) -> _Token:
        return self._tokens[self._index]

    def _advance(self) -> None:
        if self._current().kind != "EOF":
            self._index += 1

    def _match_kind(self, kind: str) -> bool:
        if self._current().kind != kind:
            return False
        self._advance()
        return True

    def _match_keyword(self, keyword: str) -> bool:
        token = self._current()
        if token.kind != "ATOM" or token.value.upper() != keyword:
            return False
        self._advance()
        return True

    def _unexpected_token_error(self, token: _Token) -> QueryValidationError:
        return QueryValidationError(
            code="invalid_token",
            message=f"Unexpected token '{token.value}'.",
            token=token.value,
            suggestions=[],
        )


def parse_query(text: str) -> QueryParseResult:
    tokens = _tokenize(text)
    parser = _Parser(tokens)
    expression = parser.parse()
    if parser.error is not None:
        return QueryParseResult(ok=False, expression=None, errors=[parser.error])

    assert expression is not None
    errors = _validate_expression(expression)
    if errors:
        return QueryParseResult(ok=False, expression=None, errors=errors)

    return QueryParseResult(ok=True, expression=expression, errors=[])


def _tokenize(text: str) -> list[_Token]:
    tokens: list[_Token] = []
    index = 0
    while index < len(text):
        character = text[index]
        if character.isspace():
            index += 1
            continue
        if character == "(":
            tokens.append(_Token(kind="LPAREN", value=character))
            index += 1
            continue
        if character == ")":
            tokens.append(_Token(kind="RPAREN", value=character))
            index += 1
            continue

        operator = _read_operator(text, index)
        if operator is not None:
            tokens.append(_Token(kind="OP", value=operator))
            index += len(operator)
            continue

        atom, index = _read_atom(text, index)
        if not atom:
            tokens.append(_Token(kind="INVALID", value=character))
            index += 1
            continue
        tokens.append(_Token(kind="ATOM", value=atom))

    tokens.append(_Token(kind="EOF", value=""))
    return tokens


def _read_operator(text: str, index: int) -> str | None:
    for operator in ("!=", ">=", "<="):
        if text.startswith(operator, index):
            return operator
    if text[index] in {"=", ">", "<", "~"}:
        return text[index]
    return None


def _read_atom(text: str, index: int) -> tuple[str, int]:
    start = index
    while index < len(text):
        character = text[index]
        if character.isspace() or character in {"(", ")", "=", ">", "<", "~", "!"}:
            break
        index += 1
    return text[start:index], index


def _validate_expression(expression: QueryExpression) -> list[QueryValidationError]:
    if isinstance(expression, QueryComparison):
        return _validate_comparison(expression)
    if isinstance(expression, QueryBinary):
        return _validate_expression(expression.left) + _validate_expression(expression.right)
    return _validate_expression(expression.operand)


def _validate_comparison(expression: QueryComparison) -> list[QueryValidationError]:
    if expression.field not in SUPPORTED_FIELDS:
        suggestions = get_close_matches(expression.field, SUPPORTED_FIELDS, n=1, cutoff=0.4)
        message = f"Unknown field '{expression.field}'."
        if suggestions:
            message += f" Did you mean '{suggestions[0]}'?"
        return [
            QueryValidationError(
                code="unknown_field",
                message=message,
                token=expression.field,
                suggestions=suggestions,
            )
        ]

    allowed_operators = ALLOWED_OPERATORS_BY_FIELD[expression.field]
    if expression.operator not in allowed_operators:
        operator_list = ", ".join(allowed_operators)
        return [
            QueryValidationError(
                code="unsupported_operator",
                message=(
                    f"Operator '{expression.operator}' is not supported "
                    f"for field '{expression.field}'. "
                    f"Allowed operators: {operator_list}."
                ),
                token=expression.operator,
                suggestions=list(allowed_operators),
            )
        ]

    if expression.field == "date" and not DATE_PATTERN.fullmatch(expression.value):
        return [
            QueryValidationError(
                code="invalid_date",
                message=(f"Invalid date value '{expression.value}'. Expected format: YYYY-MM-DD."),
                token=expression.value,
                suggestions=["YYYY-MM-DD"],
            )
        ]

    if expression.field in INTEGER_FIELDS and not _is_integer_value(expression.value):
        return [
            QueryValidationError(
                code="invalid_number",
                message=(
                    f"Invalid numeric value '{expression.value}' for field '{expression.field}'. "
                    "Expected an integer."
                ),
                token=expression.value,
                suggestions=["integer"],
            )
        ]

    if expression.field in NUMBER_FIELDS and not _is_number_value(expression.value):
        return [
            QueryValidationError(
                code="invalid_number",
                message=(
                    f"Invalid numeric value '{expression.value}' for field '{expression.field}'. "
                    "Expected a number."
                ),
                token=expression.value,
                suggestions=["number"],
            )
        ]

    return []


def _is_integer_value(value: str) -> bool:
    try:
        int(value)
    except ValueError:
        return False
    return True


def _is_number_value(value: str) -> bool:
    try:
        float(value)
    except ValueError:
        return False
    return True


def _double_operator_error(first_operator: str, second_operator: str) -> QueryValidationError:
    if first_operator == "=" and second_operator == "=":
        return QueryValidationError(
            code="invalid_operator",
            message="Unexpected operator '=' after '='. Use a single '=' for equality.",
            token="=",
            suggestions=["="],
        )

    if first_operator == ">" and second_operator == ">":
        return QueryValidationError(
            code="invalid_operator",
            message="Unexpected operator '>' after '>'. Use a single '>' or '>='.",
            token=">",
            suggestions=[">", ">="],
        )

    return QueryValidationError(
        code="invalid_operator",
        message=(f"Unexpected operator '{second_operator}' after '{first_operator}'."),
        token=second_operator,
        suggestions=[],
    )


def _missing_expression_after_boolean_error(operator: str) -> QueryValidationError:
    return QueryValidationError(
        code="missing_expression",
        message=f"Expected expression after boolean operator '{operator}'.",
        token=operator,
        suggestions=["<field><operator><value>", "("],
    )


def _invalid_boolean_pair_error(
    previous_operator: str, current_operator: str
) -> QueryValidationError:
    return QueryValidationError(
        code="invalid_boolean_pair",
        message=f"Boolean operator '{current_operator}' cannot follow '{previous_operator}'.",
        token=current_operator,
        suggestions=["NOT", "<field><operator><value>", "("],
    )
