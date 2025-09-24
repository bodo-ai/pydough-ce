# PyDough Graph: PAGILA
## Collections overview
- `film_actor`
- `address`
- `city`
- `actor`
- `category`
- `country`
- `customer`
- `film`
- `film_category`
- `inventory`
- `language`
- `rental`
- `staff`
- `payment`
- `store`
- `payment_p2022_07`
- `payment_p2022_02`
- `payment_p2022_03`
- `payment_p2022_04`
- `payment_p2022_05`
- `payment_p2022_01`
- `payment_p2022_06`

## `film_actor`
- Columns:
  - `actor_id` (numeric)
  - `film_id` (numeric)
  - `last_update` (string)
- Relationships:
  - `actor` (reverse of `actor.film_actors`)
  - `film` (reverse of `film.film_actors`)

## `address`
- Columns:
  - `address_id` (numeric)
  - `address` (string)
  - `address2` (string)
  - `district` (string)
  - `city_id` (numeric)
  - `postal_code` (string)
  - `phone` (string)
  - `last_update` (string)
- Relationships:
  - `city` (reverse of `city.addresses`)
  - `customers` → `customer` (many) (keys: address_id -> address_id)
  - `staffs` → `staff` (many) (keys: address_id -> address_id)
  - `stores` → `store` (many) (keys: address_id -> address_id)

## `city`
- Columns:
  - `city_id` (numeric)
  - `city` (string)
  - `country_id` (numeric)
  - `last_update` (string)
- Relationships:
  - `addresses` → `address` (many) (keys: city_id -> city_id)
  - `country` (reverse of `country.cities`)

## `actor`
- Columns:
  - `actor_id` (numeric)
  - `first_name` (string)
  - `last_name` (string)
  - `last_update` (string)
- Relationships:
  - `film_actors` → `film_actor` (many) (keys: actor_id -> actor_id)

## `category`
- Columns:
  - `category_id` (numeric)
  - `name` (string)
  - `last_update` (string)
- Relationships:
  - `film_categories` → `film_category` (many) (keys: category_id -> category_id)

## `country`
- Columns:
  - `country_id` (numeric)
  - `country` (string)
  - `last_update` (string)
- Relationships:
  - `cities` → `city` (many) (keys: country_id -> country_id)

## `customer`
- Columns:
  - `customer_id` (numeric)
  - `store_id` (numeric)
  - `first_name` (string)
  - `last_name` (string)
  - `email` (string)
  - `address_id` (numeric)
  - `activebool` (bool)
  - `create_date` (datetime)
  - `last_update` (string)
  - `active` (numeric)
- Relationships:
  - `addres` (reverse of `address.customers`)
  - `store` (reverse of `store.customers`)
  - `rentals` → `rental` (many) (keys: customer_id -> customer_id)
  - `payment_p2022_02s` → `payment_p2022_02` (many) (keys: customer_id -> customer_id)
  - `payment_p2022_03s` → `payment_p2022_03` (many) (keys: customer_id -> customer_id)
  - `payment_p2022_04s` → `payment_p2022_04` (many) (keys: customer_id -> customer_id)
  - `payment_p2022_05s` → `payment_p2022_05` (many) (keys: customer_id -> customer_id)
  - `payment_p2022_01s` → `payment_p2022_01` (many) (keys: customer_id -> customer_id)
  - `payment_p2022_06s` → `payment_p2022_06` (many) (keys: customer_id -> customer_id)

## `film`
- Columns:
  - `film_id` (numeric)
  - `title` (string)
  - `description` (string)
  - `release_year` (string)
  - `language_id` (numeric)
  - `original_language_id` (numeric)
  - `rental_duration` (numeric)
  - `rental_rate` (numeric)
  - `length` (numeric)
  - `replacement_cost` (numeric)
  - `rating` (string)
  - `last_update` (string)
  - `special_features` (string)
  - `fulltext` (string)
- Relationships:
  - `film_actors` → `film_actor` (many) (keys: film_id -> film_id)
  - `language` (reverse of `language.films`)
  - `language_2` (reverse of `language.films_2`)
  - `film_categories` → `film_category` (many) (keys: film_id -> film_id)
  - `inventories` → `inventory` (many) (keys: film_id -> film_id)

## `film_category`
- Columns:
  - `film_id` (numeric)
  - `category_id` (numeric)
  - `last_update` (string)
- Relationships:
  - `category` (reverse of `category.film_categories`)
  - `film` (reverse of `film.film_categories`)

## `inventory`
- Columns:
  - `inventory_id` (numeric)
  - `film_id` (numeric)
  - `store_id` (numeric)
  - `last_update` (string)
- Relationships:
  - `film` (reverse of `film.inventories`)
  - `store` (reverse of `store.inventories`)
  - `rentals` → `rental` (many) (keys: inventory_id -> inventory_id)

## `language`
- Columns:
  - `language_id` (numeric)
  - `name` (string)
  - `last_update` (string)
- Relationships:
  - `films` → `film` (many) (keys: language_id -> language_id)
  - `films_2` → `film` (many) (keys: language_id -> original_language_id)

## `rental`
- Columns:
  - `rental_id` (numeric)
  - `rental_date` (string)
  - `inventory_id` (numeric)
  - `customer_id` (numeric)
  - `return_date` (string)
  - `staff_id` (numeric)
  - `last_update` (string)
- Relationships:
  - `customer` (reverse of `customer.rentals`)
  - `inventory` (reverse of `inventory.rentals`)
  - `staff` (reverse of `staff.rentals`)
  - `payment_p2022_02s` → `payment_p2022_02` (many) (keys: rental_id -> rental_id)
  - `payment_p2022_03s` → `payment_p2022_03` (many) (keys: rental_id -> rental_id)
  - `payment_p2022_04s` → `payment_p2022_04` (many) (keys: rental_id -> rental_id)
  - `payment_p2022_05s` → `payment_p2022_05` (many) (keys: rental_id -> rental_id)
  - `payment_p2022_01s` → `payment_p2022_01` (many) (keys: rental_id -> rental_id)
  - `payment_p2022_06s` → `payment_p2022_06` (many) (keys: rental_id -> rental_id)

## `staff`
- Columns:
  - `staff_id` (numeric)
  - `first_name` (string)
  - `last_name` (string)
  - `address_id` (numeric)
  - `email` (string)
  - `store_id` (numeric)
  - `active` (bool)
  - `username` (string)
  - `password` (string)
  - `last_update` (string)
  - `picture` (string)
- Relationships:
  - `rentals` → `rental` (many) (keys: staff_id -> staff_id)
  - `addres` (reverse of `address.staffs`)
  - `store` (reverse of `store.staffs`)
  - `payment_p2022_02s` → `payment_p2022_02` (many) (keys: staff_id -> staff_id)
  - `payment_p2022_03s` → `payment_p2022_03` (many) (keys: staff_id -> staff_id)
  - `payment_p2022_04s` → `payment_p2022_04` (many) (keys: staff_id -> staff_id)
  - `payment_p2022_05s` → `payment_p2022_05` (many) (keys: staff_id -> staff_id)
  - `payment_p2022_01s` → `payment_p2022_01` (many) (keys: staff_id -> staff_id)
  - `payment_p2022_06s` → `payment_p2022_06` (many) (keys: staff_id -> staff_id)

## `payment`
- Columns:
  - `payment_id` (numeric)
  - `customer_id` (numeric)
  - `staff_id` (numeric)
  - `rental_id` (numeric)
  - `amount` (numeric)
  - `payment_date` (string)

## `store`
- Columns:
  - `store_id` (numeric)
  - `manager_staff_id` (numeric)
  - `address_id` (numeric)
  - `last_update` (string)
- Relationships:
  - `customers` → `customer` (many) (keys: store_id -> store_id)
  - `inventories` → `inventory` (many) (keys: store_id -> store_id)
  - `staffs` → `staff` (many) (keys: store_id -> store_id)
  - `addres` (reverse of `address.stores`)

## `payment_p2022_07`
- Columns:
  - `payment_id` (numeric)
  - `customer_id` (numeric)
  - `staff_id` (numeric)
  - `rental_id` (numeric)
  - `amount` (numeric)
  - `payment_date` (string)

## `payment_p2022_02`
- Columns:
  - `payment_id` (numeric)
  - `customer_id` (numeric)
  - `staff_id` (numeric)
  - `rental_id` (numeric)
  - `amount` (numeric)
  - `payment_date` (string)
- Relationships:
  - `customer` (reverse of `customer.payment_p2022_02s`)
  - `rental` (reverse of `rental.payment_p2022_02s`)
  - `staff` (reverse of `staff.payment_p2022_02s`)

## `payment_p2022_03`
- Columns:
  - `payment_id` (numeric)
  - `customer_id` (numeric)
  - `staff_id` (numeric)
  - `rental_id` (numeric)
  - `amount` (numeric)
  - `payment_date` (string)
- Relationships:
  - `customer` (reverse of `customer.payment_p2022_03s`)
  - `rental` (reverse of `rental.payment_p2022_03s`)
  - `staff` (reverse of `staff.payment_p2022_03s`)

## `payment_p2022_04`
- Columns:
  - `payment_id` (numeric)
  - `customer_id` (numeric)
  - `staff_id` (numeric)
  - `rental_id` (numeric)
  - `amount` (numeric)
  - `payment_date` (string)
- Relationships:
  - `customer` (reverse of `customer.payment_p2022_04s`)
  - `rental` (reverse of `rental.payment_p2022_04s`)
  - `staff` (reverse of `staff.payment_p2022_04s`)

## `payment_p2022_05`
- Columns:
  - `payment_id` (numeric)
  - `customer_id` (numeric)
  - `staff_id` (numeric)
  - `rental_id` (numeric)
  - `amount` (numeric)
  - `payment_date` (string)
- Relationships:
  - `customer` (reverse of `customer.payment_p2022_05s`)
  - `rental` (reverse of `rental.payment_p2022_05s`)
  - `staff` (reverse of `staff.payment_p2022_05s`)

## `payment_p2022_01`
- Columns:
  - `payment_id` (numeric)
  - `customer_id` (numeric)
  - `staff_id` (numeric)
  - `rental_id` (numeric)
  - `amount` (numeric)
  - `payment_date` (string)
- Relationships:
  - `customer` (reverse of `customer.payment_p2022_01s`)
  - `rental` (reverse of `rental.payment_p2022_01s`)
  - `staff` (reverse of `staff.payment_p2022_01s`)

## `payment_p2022_06`
- Columns:
  - `payment_id` (numeric)
  - `customer_id` (numeric)
  - `staff_id` (numeric)
  - `rental_id` (numeric)
  - `amount` (numeric)
  - `payment_date` (string)
- Relationships:
  - `customer` (reverse of `customer.payment_p2022_06s`)
  - `rental` (reverse of `rental.payment_p2022_06s`)
  - `staff` (reverse of `staff.payment_p2022_06s`)
