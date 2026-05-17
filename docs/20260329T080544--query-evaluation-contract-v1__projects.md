# Query Evaluation Contract v1

Generated: 2026-03-29T08:05:44-05:00

This document defines the **evaluation semantics** for the existing Query Grammar v1 AST.
It is a planning/spec artifact only. It does **not** define API transport, UI behavior, job orchestration, storage layout, or evaluator implementation details.

## Scope

- Applies to the existing parsed query AST produced by Query Grammar v1.
- Defines how a parsed query evaluates against a single metadata record.
- Defines evaluator truth behavior for comparisons and boolean composition.
- Does not define result ordering, pagination, service endpoints, or execution pipeline details.

## Evaluator Input Contract

- **Query input**: a valid Query Grammar v1 AST, not raw query text.
- **Record input**: one canonical metadata record with normalized field values.
- Supported fields remain: `person`, `date`, `camera`, `lens`, `iso`, `fnumber`, `focal`, `keyword`.
- `person` and `keyword` are evaluated as multi-value text fields.
- `camera` and `lens` are evaluated as single-value text fields.
- Evaluation is performed record-by-record.
- The evaluator returns a deterministic result for the same AST and the same record.

## Comparison Semantics

- text comparisons are case-insensitive.
- Text comparison behavior is defined over normalized candidate values for the referenced field.
- **text equality (`=`)**: `=` matches when any normalized field value exactly equals the query value.
- **text inequality (`!=`)**: `!=` matches when the field is present and no normalized field value equals the query value.
- **contains (`~`)**: `~` matches when the query value is a case-insensitive substring of any normalized field value.
- **ordered comparisons (`>`, `>=`, `<`, `<=`)**: apply only to fields whose values are already validated as ordered types (`date`, `iso`, `fnumber`, `focal`).
- Date comparisons operate on normalized `YYYY-MM-DD` values.
- Numeric comparisons operate on normalized numeric record values.

## Boolean Semantics

- **`AND` requires both operands to match**.
- **`OR` requires at least one operand to match**.
- **`NOT` negates the operand result**.
- Parenthesized subexpressions evaluate first according to the existing AST shape.
- Evaluation follows the parser-established grouping and precedence; the evaluator does not reinterpret syntax.

## Missing Metadata Policy

- **missing fields evaluate as non-matches**.
- If a record lacks a field referenced by a comparison, that comparison evaluates to non-match.
- empty text fields behave like fields with no candidate values and evaluate as non-matches.
- Missing values do not raise evaluator-time validation errors; malformed queries should already have been rejected by parser/validator stages.

## Evaluator Output Contract

- Minimum output is a deterministic boolean outcome for one record: `match` or `non-match`.
- Future implementations may include diagnostic detail, but the core contract for v1 is boolean record evaluation.
- The evaluator contract is intentionally separate from collection filtering, ranking, sorting, pagination, and transport envelopes.

## Canonical Evaluation Examples

### Record A

```json
{
  "person": ["alice", "bob"],
  "date": "2024-01-15",
  "camera": "Leica Q2",
  "iso": 800,
  "fnumber": 2.8,
  "keyword": ["Portrait", "Studio Light"]
}
```

- `person=alice` -> match
- `person=ALICE` -> match
- `keyword~portrait` -> match
- `keyword~studio` -> match
- `keyword!=blurred` -> match
- `date>=2024-01-01` -> match
- `person=bob` -> match
- `(person=alice OR person=bob) AND NOT keyword=blurred` -> match

### Record B

```json
{
  "person": ["bob"],
  "date": "2023-12-31",
  "camera": "Canon R6",
  "iso": 200,
  "keyword": ["blurred"]
}
```

- `person=alice` -> non-match
- `keyword~portrait` -> non-match
- `date>=2024-01-01` -> non-match
- `(person=alice OR person=bob) AND NOT keyword=blurred` -> non-match

### Record C

```json
{
  "camera": "Nikon Zf",
  "person": [],
  "keyword": []
}
```

- `person=alice` -> non-match
- `keyword~portrait` -> non-match
- `keyword!=portrait` -> non-match

## Notes

- This contract builds on the parser/validator behavior documented in `20260328T223918--query-grammar-v1-behavior__projects.md`.
- Any future implementation slice should preserve the semantics defined here unless the contract is explicitly revised first.
