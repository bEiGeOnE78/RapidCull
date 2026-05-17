# Query Grammar v1 Behavior

Generated: 2026-03-28T22:39:18-05:00

This document describes the **currently implemented parser/validator behavior** for Query Grammar v1.
It does **not** define query execution or result-set semantics.

## Supported Fields

- `person`
- `date`
- `camera`
- `lens`
- `iso`
- `fnumber`
- `focal`
- `keyword`

## Supported Operators

- Text fields (`person`, `camera`, `lens`, `keyword`): `=`, `!=`, `~`
- Ordered fields (`date`, `iso`, `fnumber`, `focal`): `=`, `!=`, `>`, `>=`, `<`, `<=`

## Boolean Logic

- Supported boolean operators: `AND`, `OR`, `NOT`
- Parentheses are supported for explicit grouping
- `NOT` binds to the following expression
- Parentheses override default boolean precedence

## Valid Examples

- `person=alice` -> ok
- `date>=2024-01-01` -> ok
- `iso>=800` -> ok
- `keyword~portrait` -> ok
- `fnumber<=2.8` -> ok
- `(person=alice OR person=bob) AND NOT keyword=blurred` -> ok

## Invalid Examples

- `people=alice` -> error:unknown_field
- `person=` -> error:missing_value
- `person>alice` -> error:unsupported_operator
- `person==alice` -> error:invalid_operator
- `date>=2024/01/01` -> error:invalid_date
- `iso>=fast` -> error:invalid_number
- `person=alice AND` -> error:missing_expression
- `person=alice AND OR person=bob` -> error:invalid_boolean_pair
- `(` -> error:missing_group_expression
- `person=alice)` -> error:unexpected_closing_parenthesis
- `(OR person=alice)` -> error:invalid_group_start

## Notes

- Errors are returned as structured parser/validation results with code, message, token, and suggestions.
- Current examples reflect the implemented `field<operator>value` grammar, not future query execution behavior.
