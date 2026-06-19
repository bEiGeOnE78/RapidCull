# Query Grammar Reference

## Overview

RapidCull's query language filters photo and video records by metadata fields such as person, date, camera, and keyword. Queries are used when creating collection views and virtual galleries. Each query expression evaluates against a single metadata record and returns a match or non-match result.

---

## Fields

| Field     | Type    | Description                                         | Example value      |
|-----------|---------|-----------------------------------------------------|--------------------|
| `person`  | text    | Recognized person name(s) tagged in the image. Multi-value: one image may have several people. | `alice`            |
| `date`    | date    | Capture date in `YYYY-MM-DD` format.                | `2024-06-01`       |
| `camera`  | text    | Camera body model. Single-value.                    | `Leica Q2`         |
| `lens`    | text    | Lens model. Single-value.                           | `85mm f/1.4`       |
| `iso`     | integer | ISO sensitivity value.                              | `800`              |
| `fnumber` | number  | Aperture f-number (decimal allowed).                | `2.8`              |
| `focal`   | number  | Focal length in mm (decimal allowed).               | `85.0`             |
| `keyword` | text    | Keyword tag(s) applied to the image. Multi-value.   | `portrait`         |

**Notes:**
- `person` and `keyword` are **multi-value** fields. An image can have multiple people or keywords. Equality (`=`) matches if any value matches; inequality (`!=`) matches only if no value matches.
- `camera` and `lens` are **single-value** fields.
- `iso` accepts integers only (`800`, not `800.0`).
- `fnumber` and `focal` accept integers or decimals (`2.8`, `85`, `1.4`).
- Missing fields evaluate as **non-match** — a record without a `lens` field will not match `lens=50mm`.

---

## Operators

### Text operators (`person`, `camera`, `lens`, `keyword`)

| Operator | Name          | Description                                                                 |
|----------|---------------|-----------------------------------------------------------------------------|
| `=`      | Equals        | Case-insensitive exact match. For multi-value fields, matches if any value equals the query value. |
| `!=`     | Not equals    | Case-insensitive. For multi-value fields, matches only if no value equals the query value. |
| `~`      | Contains      | Case-insensitive substring match. Matches if the query value appears anywhere in any field value. |

### Ordered operators (`date`, `iso`, `fnumber`, `focal`)

| Operator | Name                  | Description                              |
|----------|-----------------------|------------------------------------------|
| `=`      | Equals                | Exact match (case-sensitive for dates).  |
| `!=`     | Not equals            | Does not equal.                          |
| `>`      | Greater than          | Record value is strictly greater.        |
| `>=`     | Greater than or equal | Record value is greater than or equal.   |
| `<`      | Less than             | Record value is strictly less.           |
| `<=`     | Less than or equal    | Record value is less than or equal.      |

Using an ordered operator on a text field (e.g., `person>alice`) produces an `unsupported_operator` error. Using a text-only operator on an ordered field (e.g., `iso~800`) is also an error.

---

## Boolean Logic

Queries can combine multiple comparisons using `AND`, `OR`, and `NOT`. Boolean keywords are case-insensitive (`and`, `AND`, `And` all work).

| Keyword | Description                                         |
|---------|-----------------------------------------------------|
| `AND`   | Both operands must match.                           |
| `OR`    | At least one operand must match.                    |
| `NOT`   | Negates the following expression.                   |

**Parentheses** group sub-expressions to control evaluation order. Without parentheses, the parser handles `NOT` first (tightest binding), then `AND`, then `OR`.

```
person=alice AND keyword=portrait
(person=alice OR person=bob) AND NOT keyword=blurred
NOT (iso<400 OR fnumber>4.0)
```

---

## Examples

### 1. Exact person match
```
person=alice
```
Matches any record where `alice` appears in the person list (case-insensitive).

### 2. Date range — after a specific date
```
date>=2024-01-01
```
Matches records captured on or after 2024-01-01.

### 3. Date range — within a year
```
date>=2024-01-01 AND date<2025-01-01
```
Matches records captured during calendar year 2024.

### 4. ISO ceiling for low-noise shots
```
iso<=400
```
Matches records with ISO 400 or lower.

### 5. Wide-aperture shots
```
fnumber<=2.8
```
Matches records shot at f/2.8 or wider (lower f-number = wider aperture).

### 6. Keyword substring match
```
keyword~studio
```
Matches records where any keyword contains the substring `studio` (e.g., `Studio Light`, `outdoor-studio`).

### 7. Either of two people
```
person=alice OR person=bob
```
Matches records that include alice, bob, or both.

### 8. People in portraits, excluding blurred shots
```
(person=alice OR person=bob) AND NOT keyword=blurred
```
Matches records of alice or bob that do not have the keyword `blurred`.

### 9. Specific camera body
```
camera=Leica Q2
```
Matches records where the camera field is exactly `Leica Q2` (case-insensitive).

### 10. Portraits with fast glass on a specific camera
```
camera~Canon AND fnumber<=1.8 AND keyword=portrait
```
Matches records from any Canon camera body, shot at f/1.8 or wider, tagged `portrait`.

---

## Error Messages

Invalid queries return a structured error with a `code`, `message`, `token`, and `suggestions` list. Common errors:

### Unknown field
```
people=alice
```
**Error** (`unknown_field`): `Unknown field 'people'. Did you mean 'person'?`
Suggestions include close matches from the supported field list.

### Unsupported operator for field
```
person>alice
```
**Error** (`unsupported_operator`): `Operator '>' is not supported for field 'person'. Allowed operators: =, !=, ~.`

### Invalid date format
```
date>=2024/06/01
```
**Error** (`invalid_date`): `Invalid date value '2024/06/01'. Expected format: YYYY-MM-DD.`

### Non-numeric value for numeric field
```
iso>=fast
```
**Error** (`invalid_number`): `Invalid numeric value 'fast' for field 'iso'. Expected an integer.`

### Missing value after operator
```
person=
```
**Error** (`missing_value`): `Expected value after operator '='.`

### Incomplete boolean expression
```
person=alice AND
```
**Error** (`missing_expression`): `Expected expression after boolean operator 'AND'.`

### Mismatched parentheses
```
(person=alice
```
**Error** (`mismatched_parentheses`): `Missing closing ')' for grouped expression.`

### Unexpected closing parenthesis
```
person=alice)
```
**Error** (`unexpected_closing_parenthesis`): `Unexpected closing ')' with no matching opening '('.`
