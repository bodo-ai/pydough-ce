PyDough DSL — Prompt Authoring Guide

Purpose
- Translate analytics questions into executable PyDough code that assigns the final collection to `result`.
- Operate strictly on the provided metadata: collections, properties, relationships.

Hard Rules
- Return ONLY Python code using the PyDough DSL; assign the final expression to `result`.
- No imports, filesystem access, or plain pandas/SQL. Keep logic declarative.
- Use exact identifiers (case-sensitive) as shown in the metadata section.

Core Concepts
- Collection: table-like entity (e.g., `sales`, `customers`).
- Property: scalar column of a collection (e.g., `amount`, `city`). Reference directly inside expressions; do not prefix with the collection name inside `CALCULATE`/`WHERE`.
- Relationship: navigation to related sub-collections via attributes (e.g., `customers.orders`). Aggregate functions operate on plural sub-collections.

Key Operations
- CALCULATE – projection/derivations:
  `result = sales.CALCULATE(city, amount)`

- WHERE – filtering:
  `result = sales.WHERE(city == "New York").CALCULATE(city, amount)`

- TOP_K – top-k with ordering:
  `result = sales.CALCULATE(city, amount).TOP_K(3, by=amount.DESC())`

- ORDER_BY – general ordering:
  `result = sales.CALCULATE(city, amount).ORDER_BY(city.ASC(), amount.DESC())`

- Aggregations – SUM, COUNT, AVG, MIN, MAX:
  - On the current collection:
    `result = sales.CALCULATE(city, total_amount=SUM(amount)).TOP_K(5, by=total_amount.DESC())`
  - Over a relationship:
    `result = customers.CALCULATE(name, total_spend=SUM(orders.amount))`

- Existence – HAS / HASNOT:
  `result = customers.HAS(orders.WHERE(amount > 0)).CALCULATE(name)`

Date Helpers
- Use only for datetime properties: `YEAR(created) == 2024`, `MONTH(created) == 1`.

Reliable Templates
1) Top-K rows by a numeric column
```
result = sales.CALCULATE(city, amount).TOP_K(3, by=amount.DESC())
```

2) Filter then project
```
result = sales.WHERE(city == "Chicago").CALCULATE(city, amount)
```

3) Multi-key sort
```
result = sales.CALCULATE(city, amount).ORDER_BY(city.ASC(), amount.DESC())
```

4) Grouped totals (single table)
```
result = sales.CALCULATE(city, total_amount=SUM(amount)).TOP_K(10, by=total_amount.DESC())
```

5) Relationship aggregation
```
result = customers.CALCULATE(name, order_count=COUNT(orders), total_spend=SUM(orders.amount))
```

Pitfalls & Fixes
- Expected a collection, but received an expression → Apply methods to collections and use CALCULATE for projections; TOP_K acts on collections.
- Unrecognized term / name → Use identifiers exactly as in metadata; avoid `collection.property` inside CALCULATE.
- Aggregation mixes context and subcollection → Aggregate from the iterated collection’s perspective (e.g., `SUM(orders.amount)` in the parent) and don’t reference parent scalars inside the aggregate argument.

Response Format
- The LLM response should be JSON with `code` (and optional `explanation`). The code must assign the final collection to `result`.

