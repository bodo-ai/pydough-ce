# PyDough Graph: ANALYTICS
## Collections overview
- `cities`
- `payments`

## `cities`
- Columns:
  - `id` (numeric)
  - `name` (string)
- Relationships:
  - `payment` → `payments` (many) (keys: id -> city_id)

## `payments`
- Columns:
  - `id` (numeric)
  - `city_id` (numeric)
  - `amount` (numeric)
  - `paid_at` (string)
- Relationships:
  - `city` (reverse of `cities.payment`)
