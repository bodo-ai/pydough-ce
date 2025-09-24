from __future__ import annotations

# High-signal PyDough guide used to steer LLM code generation.

PYDOUGH_GUIDE = r"""
PyDough DSL – Authoring Guide

Purpose
- Translate analytics questions into executable PyDough code that returns a tabular collection assigned to `result`.
- Operate strictly on the provided metadata: collections, properties, relationships.

Hard Rules
- Return ONLY Python code using the PyDough DSL and assign the final collection to `result`.
- Do NOT import modules, access files, or use plain pandas/SQL.
- Chain PyDough methods; avoid Python loops/ifs outside of expressions.
- Use exact identifiers (case-sensitive) as shown in metadata.

Core Concepts
- Collection: a table-like entity (e.g., `sales`, `customers`).
- Property: a scalar column on a collection (e.g., `amount`, `city`). Use directly inside expressions; do not prefix with the collection name inside `CALCULATE` or `WHERE`.
- Relationship: navigation to related sub-collections via attributes (e.g., `orders.customer`, `customer.orders`). Aggregations operate on plural sub-collections.

Essential Operations
- CALCULATE: project columns and derived expressions.
  result = sales.CALCULATE(city, amount)

- WHERE: filter a collection.
  result = sales.WHERE(city == "New York").CALCULATE(city, amount)

- TOP_K: return top-k rows ordered by an expression; usually applied to the result of CALCULATE.
  result = sales.CALCULATE(city, amount).TOP_K(3, by=amount.DESC())

- ORDER_BY: general ordering (ascending/descending) without limiting.
  result = sales.CALCULATE(city, amount).ORDER_BY(city.ASC(), amount.DESC())

- Aggregations: SUM, COUNT, AVG, MIN, MAX over plural sub-collections or current collection rows.
  - Grouped metric on current collection:
    result = sales.CALCULATE(city, total_amount=SUM(amount)).TOP_K(5, by=total_amount.DESC())
  - Aggregating over a relationship (plural):
    result = customers.CALCULATE(
        name,
        order_count=COUNT(orders),
        total_spend=SUM(orders.amount)
    ).TOP_K(10, by=total_spend.DESC())

- Existence tests: HAS / HASNOT for sub-collection conditions.
  result = customers.HAS(orders.WHERE(amount > 0)).CALCULATE(name)

Date/Time Helpers (examples; use only if properties are datetime)
- YEAR(created) == 2024, MONTH(created) == 1, DAY(created) == 15

Reliable Patterns
1) Top-K rows by a numeric column:
   result = sales.CALCULATE(city, amount).TOP_K(3, by=amount.DESC())

2) Filter then project:
   result = sales.WHERE(city == "Chicago").CALCULATE(city, amount)

3) Multi-key sort:
   result = sales.CALCULATE(city, amount).ORDER_BY(city.ASC(), amount.DESC())

4) Simple grouped totals (single table):
   result = sales.CALCULATE(city, total_amount=SUM(amount)).TOP_K(10, by=total_amount.DESC())

5) Relationship aggregation:
   result = customer.CALCULATE(name, total_spend=SUM(orders.amount))

Naming & Referencing
- Inside CALCULATE, reference properties directly (e.g., `amount`, not `sales.amount`).
- When ranking by a calculated metric, reference the alias directly (e.g., `by=total_amount.DESC()`).
- Do not reuse a collection name as a calculated field.

Common Pitfalls & Fixes
- "Expected a collection, but received an expression":
  Ensure you call methods on a collection (e.g., `sales.WHERE(...).CALCULATE(...)`) and apply `TOP_K` to a collection, not to a scalar.

- "Unrecognized term" or name errors:
  Use identifiers exactly as in metadata; avoid prefixing properties with the collection name.

- Aggregation error mentioning "mix between subcollection data and fields of the context":
  Phrase the aggregated expression from the perspective of the iterated collection. For single tables, `SUM(amount)` is valid; for relationships, aggregate from the child path (e.g., `SUM(orders.amount)`) and avoid referencing parent fields inside the aggregate argument.

Response Requirements
- Output must be JSON per system instruction with a `code` field containing valid Python. The code must end with assigning the final collection to `result`.

Short Examples
```python
# Top 3 cities by total amount
result = sales.CALCULATE(
    city,
    total_amount=SUM(amount)
).TOP_K(3, by=total_amount.DESC())

# New York sales, highest first
result = sales.WHERE(city == "New York").CALCULATE(city, amount).TOP_K(10, by=amount.DESC())

# Sort by city asc then amount desc
result = sales.CALCULATE(city, amount).ORDER_BY(city.ASC(), amount.DESC())
```
"""

__all__ = ["PYDOUGH_GUIDE"]

