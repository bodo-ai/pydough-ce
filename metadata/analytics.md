# PyDough Graph: ANALYTICS
## Collections overview
- `cities`
- `payments`

## `cities`
- Columns:
  - `city_id` (numeric)
  - `city_name` (string)
- Relationships:
  - `payment` → `payments` (many) (keys: city_id -> city_id)

## `payments`
- Columns:
  - `payment_id` (numeric)
  - `city_id` (numeric)
  - `amount` (numeric)
  - `paid_at` (string)
- Relationships:
  - `city` (reverse of `cities.payment`)
