## **PYDOUGH CHEAT SHEET**  
The examples shown are not from the current database schema; just treat them as examples and make sure to use the right schema. EXAMPLE_GRAPH is just an example of a high level graph.

### **GENERAL RULES**: 

  - You should use `HAS` function to verify the 1 to N relationship beetwen tables, and you can identify them because the related subcollection has a plural name. For example, for the query "Give the number of orders for every nation", you solve like this: `nations.WHERE(HAS(customers.orders)==1).CALCULATE(nation_name=name, num_of_orders=COUNT(customers.orders.key))`.

  - This is NOT SQL, so don't make assumptions about its syntax or behavior.

  - Always use TOP_K instead of ORDER_BY when you need to order but also select a the high, low or an specific "k" number of records.

  - If a query does not specify an specific year, and want that you calculate for all the year, for example “compare year over year”, then the requested calculation must be performed for each year available in TPC: 1995, 1996, 1995 and 1998. You need to use SINGULAR function to call every year in the final result. 

  - If you need to use an attribute of a previous collection, you must have calculated the attribute using CALCULATE.

  - CALCULATE ONLY supports singular expressions. If you need to use plural sub-collections, you MUST use aggregation functions. Plural sub-collections refer to collections that have a one-to-many or many-to-many relationship.
  
  - RANKING is used as a function instead of method.

  - When using functions like TOP_K, ORDER_BY, you must ALWAYS provide an expression, not a collection. Ensure that the correct type of argument is passed. For example, `supp_group.TOP_K(3, total_sales.DESC(na_pos='last')).CALCULATE(supplier_name=supplier_name, total_sales=total_sales)` is invalid because TOP_K expects an expression, not a collection. The “by” parameter must never have collections or subcollections 

  - PARTITION function ALWAYS need 2 parameters `name and by`. The “by” parameter must never have collections, subcollections or calculations. Any required variable or value must have been previously calculated, because the parameter only accept expressions. PARTITION does not support receiving a collection; you must ALWAYS provide an expression, not a collection. For example, you cannot do: `nations.PARTTION(name="nation", by=(name)).CALCULATE(nation_name=name,top_suppliers=nation.suppliers.TOP_K(3, by=SUM(lines.extended_price).DESC())` because TOP_K returns a collection.

  - PARTITION must always be used as a method. Never do PARTITION by the key or the collection key.
  
  - CALCULATE function ALWAYS needs an expression, not a collection. For example, you cannot do: `nations.CALCULATE(nation_name=name, top_suppliers=suppliers.TOP_K(3, by=SUM(lines.extended_price).DESC())` because TOP_K returns a collection. 

  - In PyDough, complex calculations can often be expressed concisely by combining filters, transformations, and aggregations at the appropriate hierarchical level. Instead of breaking problems into multiple intermediate steps, leverage CALCULATE to directly aggregate values, use WHERE to filter data at the correct scope, and apply functions like SUM or TOP_K at the highest relevant level of analysis. Avoid unnecessary partitioning or intermediate variables unless absolutely required, and focus on composing operations hierarchically to streamline solutions while maintaining clarity and efficiency.

  - PyDough does not support use different childs in operations, for example you cannot do: `total_order_value = SUM(orders.lines.extended_price * (1 - orders.lines.discount))` because you have two different calls. Instead use CALCULATE with a variable, for example: `total_order_value = SUM(orders.lines.CALCULATE(total_order_value = extended_price * (1 - discount)).total_order_value)`.

  - If you need to get the best rankings within a CALCULATE method, you can use the RANKING method instead of TOP_K, and then filter them by the ranking number.

## **1. COLLECTIONS & SUB-COLLECTIONS**  

### **Syntax** 
Access collections/sub-collections using dot notation.  

### **Examples**:  
  - `People` → Access all records in the 'People' collection.  
  - `People.current_address` → Access current addresses linked to people.  
  - `Packages.customer` → Access customers linked to packages.  

## **2. CALCULATE EXPRESSIONS**  

### **Purpose**
Derive new fields, rename existing ones or select specific fields.  

### **Syntax**
Collection.CALCULATE(field=expression, ...)  

### **Examples**:  

  - **Select fields**:  
    ``` 
    People.CALCULATE(first_name=first_name, last_name=last_name)
    ```

  - **Derived fields**:
    ```   
    Packages.CALCULATE(  
        customer_name=JOIN_STRINGS(' ', customer.first_name, customer.last_name),  
        cost_per_unit=package_cost / quantity  
    )
    ```

### **Rules**  
  - Use aggregation functions (e.g., SUM, COUNT) for plural sub-collections.

  - Positional arguments must precede keyword arguments.

  - New fields defined in a CALCULATE do not take effect until after the CALCULATE completes. If you want to access the new field defined, you must use CALCULATE again to reference it.

  - Existing new fields not included in a CALCULATE can still be referenced but are not part of the final result unless included in the last CALCULATE clause.

  - A CALCULATE on the graph itself creates a collection with one row and columns corresponding to the properties inside the CALCULATE. 

## **3. FILTERING (WHERE)**  

### **Syntax** 
.WHERE(condition)  

### **Examples** 

  - **Filter people with negative account balance**:  
    ``` 
    People.WHERE(acctbal < 0)
    ```  

  - **Filter packages ordered in 2023**  
    ``` 
    Packages.WHERE(YEAR(order_date) == 2023)
    ``` 

  - **Filter addresses with occupants** 
    ``` 
    Addresses.WHERE(HAS(current_occupants)==1)
    ```  

### **Rules**  
  - Use & (AND), | (OR), ~ (NOT) instead of and, or, not.  
  - Avoid chained comparisons (e.g., replace a < b < c with (a < b) & (b < c)).

## **4. SORTING (ORDER_BY)**  

### **Syntax** 
  .ORDER_BY(field.ASC()/DESC(), ...)  

### **Parameters**  

  .ASC(na_pos='last') → Sort ascending, nulls last.  

  .DESC(na_pos='first') → Sort descending, nulls first.

### **Examples** 

  - **Alphabetical sort**:
    ``` 
    People.ORDER_BY(last_name.ASC(), first_name.ASC())
    ```

  - **Most expensive packages first**:  
    ``` 
    Packages.ORDER_BY(package_cost.DESC())
    ```  

## **5. SORTING TOP_K(k, by=field.DESC())**  

### **Purpose**
Select top k records.

### **Syntax**  
  .TOP_K(k, by=field.DESC())

### **Example** 
  Top 10 customers by orders count:
  ``` 
  customers.TOP_K(10, by=COUNT(orders).DESC())
  ```

  Top 10 customers by orders count (but also selecting only the name):
  ```   
  customers.CALCULATE(cust_name=name).TOP_K(10, by=COUNT(orders).DESC())
  ```

### **Rules**
- The two parameters are obligatory.

## **6. AGGREGATION FUNCTIONS**  

### **Functions**
- **HAS(collection)**: True if ≥1 record exists.  
  Example: HAS(People.packages)==1

- **HASNOT(collection)**: True if collection is empty.
  Example: HASNOT(orders)==1
  
- **COUNT(collection)**: Count non-null records.  
  Example: COUNT(People.packages)  

- **SUM(collection)**: Sum values.  
  Example: SUM(Packages.package_cost)  

- **AVG(collection)**: Average values.  
  Example: AVG(Packages.quantity)  

- **MIN/MAX(collection)**: Min/Max value.  
  Example: MIN(Packages.order_date)  

- **NDISTINCT(collection)**: Distinct count.  
  Example: NDISTINCT(Addresses.state)  

- **MEDIAN(collection.attribute)**: Takes the median of the plural set of numerical values it is called on. Note: absent records are ignored when deriving the median.
  Example:Customers.CALCULATE(name,median_order_price = MEDIAN(orders.total_price))

### **Rules** 
Aggregations Function does not support calling aggregations inside of aggregations

## **7. PARTITION**

### **Purpose**
Group records by keys.  

### **Syntax**
PARTITION(name='group_name', by=(key1, key2))  

### **Rules**: 
- All the parameters in "by=(key1, key2)" must be use in CALCULATE without using the "name" of the PARTITION.
- Partition keys must be scalar fields from the collection. 
- You must use Aggregation functions to call plural values inside PARTITION.

### **Good Examples**  

  - **Group addresses by state and count occupants**: 
    ```  
    Addresses.PARTITION(name="states", by=(state)).CALCULATE(
    state,
    n_people=COUNT(Addresses.current_occupants)
    )
    ```  
    **IMPORTANT**: Look here, where we do not need to use  "Addresses.state", we only use "state", because this is in the "by" sentence. 

  - **Group packages by year/month**:  
    ```
    package_info = Packages.CALCULATE(order_year=YEAR(order_date), order_month=MONTH(order_date))
    package_info.PARTITION(name='packs', by=(order_year, order_month))
    ```  
  - **For every year/month, find all packages that were below the average cost of all packages ordered in that year/month.**:  Notice how the version of `Packages` that is the sub-collection of the `months` can access `avg_package_cost`, which was defined by its ancestor (at the `PARTITION` level).
    ``` 
    package_info = Packages.CALCULATE(order_year=YEAR(order_date), order_month=MONTH(order_date))
    package_info.PARTITION(name="months", by=(order_year, order_month)).CALCULATE(
        avg_package_cost=AVG(Packages.package_cost)
    ).Packages.WHERE(
        package_cost < avg_package_cost
    )
    ```
    **IMPORTANT**: Look here, we can access the collection after the partition using the collection name. This is useful when you need to access a previously defined field or when you need the partitioned data.

  - **For every customer, find the percentage of all orders made by current occupants of that city/state made by that specific customer. Includes the first/last name of the person, the city/state they live in, and the percentage.**:  Notice how the version of `Addresses` that is the sub-collection of the `cities` can access `total_packages`, which was defined by its ancestor (at the `PARTITION` level). and notice we can defined more variables with CALCULATE.
    ``` 
    Addresses.WHERE(
      HAS(current_ocupants)==1
    ).PARTITION(name="cities", by=(city, state)).CALCULATE(
        total_packages=COUNT(Addresses.current_occupants.packages)
    ).Addresses.CALCULATE(city, state).current_occupants.CALCULATE(
        first_name,
        last_name,
        city=city,
        state=state,
        pct_of_packages=100.0 * COUNT(packages) / total_packages,
    )
    ```
  - **For every part of the market segment find the total quantity sold**: Notice that you need to access the lines collection again after performing the PARTITION in part_totals_per_segment. After applying PARTITION, it’s necessary to re-access the collection is you a data from the collection.
    ```
    # Step 1: Filter lines for 1998 and gather necessary info (segment, part name)
    # Navigate from lines -> order -> customer -> mktsegment and lines -> part -> name
    lines_1998_info = lines.WHERE(YEAR(order.order_date) == 1998).CALCULATE(
        mktsegment = order.customer.mktsegment,
        part_name = part.name
    )

    # Step 2: Group by market segment and part name, summing the quantity
    # PARTITION the filtered lines info by segment and part name
    part_totals_per_segment = lines_1998_info.PARTITION(
        name="part_segment_groups", by=(mktsegment, part_name)
    ).CALCULATE(
        mktsegment = mktsegment,
        part_name = part_name,
        # SUM the quantity from the original collection context within the PARTITION group
        total_quantity = SUM(lines.quantity)
    )
    ```
  - **Good Example #1**: Find every unique state.
    ```
    Addresses.PARTITION(name="states", by=state).CALCULATE(Addresses)
    ```

  - **Good Example #2**: For every city/state, count how many people live in that city/state.
    ```
    Addresses.PARTITION(name="cities", by=(city, state)).CALCULATE(
        state,
        city,
        n_people=COUNT(Addresses.current_occupants)
    )
    ```

  - **Good Example #3**: Find the top 5 years with the most people born in that year who have yahoo email accounts, listing the year and the number of people.
    ```
    yahoo_people = People.CALCULATE(
        birth_year=YEAR(birth_date)
    ).WHERE(ENDSWITH(email, "@yahoo.com"))
    yahoo_people.PARTITION(name="years", by=birth_year).CALCULATE(
        birth_year,
        n_people=COUNT(People)
    ).TOP_K(5, by=n_people.DESC())
    ```

  - **Good Example #4**: Identify the states whose current occupants account for at least 1% of all packages purchased. List the state and the percentage. Notice how `total_packages` is down-streamed from the graph-level `CALCULATE`.
  ```
  EXAMPLE_GRAPH.CALCULATE(
      total_packages=COUNT(Packages)
  ).Addresses.WHERE(
    HAS(current_occupants.package) == 1
  ).PARTITION(name="states", by=state).CALCULATE(
      state,
      pct_of_packages=100.0 * COUNT(Addresses.current_occupants.package) / total_packages
  ).WHERE(pct_of_packages >= 1.0)
  ```

  - **Good Example #5**: Identify which months of the year have numbers of packages shipped in that month that are above the average for all months.
  ```
  pack_info = Packages.CALCULATE(order_month=MONTH(order_date))
  month_info = pack_info.PARTITION(name="months", by=order_month).CALCULATE(
      n_packages=COUNT(Packages)
  )
  EXAMPLE_GRAPH.CALCULATE(
      avg_packages_per_month=AVG(month_info.n_packages)
  ).PARTITION(pack_info, name="months", by=order_month).CALCULATE(
      month,
  ).WHERE(COUNT(Packages) > avg_packages_per_month)
  ```

  - **Good Example #6**: Find the 10 most frequent combinations of the state that the person lives in and the first letter of that person's name. Notice how `state` can be used as a partition key of `people_info` since it was made available via down-streaming.
  ```
  people_info = Addresses.WHERE(
    HAS(current_occupants) == 1
  ).CALCULATE(state).current_occupants.CALCULATE(
      first_letter=first_name[:1],
  )
  people_info.PARTITION(name="combinations", by=(state, first_letter)).CALCULATE(
      state,
      first_letter,
      n_people=COUNT(current_occupants),
  ).TOP_K(10, by=n_people.DESC())
  ```

  - **Good Example #7**: Same as good example #8, but written differently so it will include people without a current address (their state is listed as `"N/A"`).
  ```
  people_info = People.CALCULATE(
      state=DEFAULT_TO(current_address.state, "N/A"),
      first_letter=first_name[:1],
  )
  people_info.PARTITION(name="state_letter_combos", by=(state, first_letter)).CALCULATE(
      state,
      first_letter,
      n_people=COUNT(People),
  ).TOP_K(10, by=n_people.DESC())
  ```

  - **Good Example #8**: Partition the current occupants of each address by their birth year and filter to include individuals born in years with at least 10,000 births. For each such person, list their first/last name and the state they live in. This is valid because `state` was down-streamed to `people_info` before it was partitioned, so when `current_occupants` is accessed as a sub-collection of the `years`, it still has access to `state`.
  ```
  people_info = Addresses.WHERE(
    HAS(current_occupants)==1
  ).CALCULATE(state).current_occupants.CALCULATE(birth_year=YEAR(birth_date))
  people_info.PARTITION(name="years", by=birth_year).WHERE(
      COUNT(current_occupants) >= 10000
  ).current_occupants.CALCULATE(
      first_name,
      last_name,
      state
  )
  ```

  - **Good Example #9**: Find all packages that meet the following criteria: they were ordered in the last year that any package in the database was ordered, their cost was below the average of all packages ever ordered, and the state it was shipped to received at least 10,000 packages that year.
  ```
  EXAMPLE_GRAPH.CALCULATE(
      avg_cost=AVG(Packages.package_cost),
      final_year=MAX(Packages.order_year),
  ).Packages.CALCULATE(
      order_year=YEAR(order_date),
      shipping_state=shipping_address.state
  ).WHERE(order_year == final_year
  ).PARTITION(
      name="states",
      by=shipping_state
  ).WHERE(
      COUNT(Packages) > 10000
  ).Packages.WHERE(
      package_cost < avg_cost
  ).CALCULATE(
      shipping_state,
      package_id,
      order_date,
  )
  ```

  - **Good Example #10**: For each state, finds the largest number of packages shipped to a single city in that state. This is done by first partitioning the packages by the city/state of the shipping address, with the name `cities`, then partitioning the result again on `states` with the name `states`. The `states` partition collection is able to access the data from the first partition as a sub-collection with the name `cities`.
  ```
  pack_info = Addresses.CALCULATE(city, state).packages_shipped_to
  city_groups = pack_info.PARTITION(
      name="cities", by=(city, state)
  ).CALCULATE(n_packages=COUNT(packages_shipped_to))
  city_groups.PARTITION(
      name="states", by=state
  ).CALCULATE(state, max_packs=MAX(cities.n_packages))
  ```

### **Bad Examples**
  - **Partition people by their birth year to find the number of people born in each year**: Invalid because the `email` property is referenced, which is not one of the partition keys, even though the data being partitioned does have an `email` property.
    ```
    People.CALCULATE(birth_year=YEAR(birth_date)).PARTITION(name="years", by=birth_year).CALCULATE(
    birth_year,
    email,
    n_people=COUNT(People)
  )
    ```

  - **Count how many packages were ordered in each year**: Invalid because `YEAR(order_date)` is not allowed to be used as a partition term (it must be placed in a `CALCULATE` so it is accessible as a named reference).
    ```
    Packages.PARTITION(name="years", by=YEAR(order_date)).CALCULATE(
    n_packages=COUNT(Packages)
    )
    ```

  - **Count how many people live in each state**: Invalid because `current_address.state` is not allowed to be used as a partition term (it must be placed in a `CALCULATE` so it is accessible as a named reference).
    ``` 
    People.PARTITION(name="state", by=current_address.state).CALCULATE(
    n_packages=COUNT(People)
    )
    ```
  - **Partition people by their birth year to find the number of people born in each year.**: Invalid because the `People.email` property is referenced, which is plural with regards to the `years` collection and thus cannot be referenced in a calculate unless it is aggregated.
  ```
  People.CALCULATE(birth_year=YEAR(birth_date)).PARTITION(name="years", by=birth_year).CALCULATE(
      birth_year,
      People.email,
      n_people=COUNT(People)
  )
  ```

  **Bad Example #1**: Invalid version of good example #7 that did not use a `CALCULATE` to make `state` available via down-streaming or to bind `first_name[:1]` to a name, therefore neither can be used as a partition term.
  ```
  Addresses.current_occupants.PARTITION(name="combinations", by=(state, first_name[:1])).CALCULATE(
      state,
      first_name[:1],
      n_people=COUNT(current_occupants),
  ).TOP_K(10, by=n_people.DESC())
  ```

  - **Bad Example #2**: Partition people by their birth year to find the number of people born in each year. Invalid because the `email` property is referenced, which is not one of the partition keys, even though the data being partitioned does have an `email` property.
  ```
  People.CALCULATE(birth_year=YEAR(birth_date)).PARTITION(name="years", by=birth_year).CALCULATE(
      birth_year,
      email,
      n_people=COUNT(People)
  )
  ```

  - **Bad Example #9**: Invalid version of good example #7 that accesses the sub-collection of `combinations` with the wrong name `Addresses` instead of `current_occupants`.
  ```
  people_info = Addresses.CALCULATE(state).current_occupants.CALCULATE(
      first_letter=first_name[:1],
  )
  people_info.PARTITION(name="combinations", by=(state, first_letter)).CALCULATE(
      state,
      first_letter,
      n_people=COUNT(Addresses),
  ).TOP_K(10, by=n_people.DESC())
  ```

## **8. WINDOW FUNCTIONS**  

Window functions in PyDough have an optional `per` argument. If this argument is omitted, it means that the window function applies to all records of the current collection (e.g. rank all customers). If it is provided, it should be a string that describes which ancestor of the current context the window function should be calculated with regards to, and in that case it means that the set of values used by the window function should be per-record of the correspond ancestor (e.g. rank all customers per-nation).

If there are multiple ancestors of the current context with the same name, the `per` string should include a suffix `:idx` where `idx` specifies which ancestor with that name to use (`1` = the most recent, `2` = the 2nd most recent, etc.) For example, consider the following:

```
order_info = Orders.CALCULATE(y=YEAR(order_date), m=MONTH(order_date))
p1 = order_info.PARTITION(name="groups", by=(y, m))
p2 = p1.(name="groups", by=(y))
data = p2.groups.Orders

# Ranks each order per year/month by its total price.
# The full ancestry is p2 [name=groups] -> p1 [name=groups] -> order_info [name=Orders],
# So "groups:1" means the window function should be computed with regards to p1
# since it is the most recent ancestor with the name "groups".
data.CALCULATE(r=RANKING(by=total_price.DESC(), per="groups:1"))

# Ranks each order per year by its total price.
# The full ancestry is p2 [name=groups] -> p1 [name=groups] -> order_info [name=Orders],
# So "groups:2" means the window function should be computed with regards to p2
# since it is the 2nd most recent ancestor with the name "groups".
data.CALCULATE(r=RANKING(by=total_price.DESC(), per="groups:2"))
```
### **RANKING:**  
#### **Syntax**
RANKING(by=field.DESC(), per='collection', allow_ties=False)  

#### **Parameters**
    
- by: Ordering criteria (e.g., acctbal.DESC()).
        
- per: Hierarchy level (e.g.,per="nation" for per-nation ranking). Must be an ancestor of the current context.
        
- allow\_ties (default False): Allow tied ranks.
        
- dense (default False): Use dense ranking.
        
#### **Examples**
``` 
# Rank every customer relative to all other customers byacctbal
Regions.nations.customers.CALCULATE(r=RANKING(by=acctbal.DESC()))

# Rank every customer relative to other customers in the same nation, by acctbal
Regions.nations.customers.CALCULATE(r=RANKING(by=acctbal.DESC(), per="nations"))

# Rank every customer relative to other customers in the same region, by acctbal
Regions.nations.customers.CALCULATE(r=RANKING(by=acctbal.DESC(), per="Regions"))

# Rank customers per-nation by their account balance
# (highest = rank #1, no ties)
Nations.customers.CALCULATE(r = RANKING(by=acctbal.DESC(), per="Nations"))

# For every customer, finds their most recent order
# (ties allowed)
Customers.orders.WHERE(RANKING(by=order_date.DESC(), per="Customers", allow_ties=True) == 1)
```

### **PERCENTILE:**  

#### **Syntax**
PERCENTILE(by=field.ASC(), n_buckets=100, per="name_antecesor")  

#### **Parameters**
    
- by: Ordering criteria.
        
- `per` (optional): optional argument (default `None`) for the same `per` argument as all other window functions.
        
- n\_buckets (default 100): Number of percentile buckets.
        
#### **Example**
``` 
# Keep the top 0.1% of customers with the highest account balances.
Customers.WHERE(PERCENTILE(by=acctbal.ASC(), n_buckets=1000) == 1000)

# For every region, find the top 5% of customers with the highest account balances.
Regions.nations.customers.WHERE(PERCENTILE(by=acctbal.ASC(), per="Regions") > 95)
```

### **RELSUM:**

The `RELSUM` function returns the sum of multiple rows of a singular expression within the same collection, e.g. the global sum across all rows, or the sum of rows per an ancestor of a sub-collection. The arguments:

#### **Parameters:**
- `expression`: the singular expression to take the sum of across multiple rows.
- `per` (optional): optional argument (default `None`) for the same `per` argument as all other window functions.
- `by` (optional): 1+ collation values, either as a single expression or an iterable of expressions, used to order the records of the current context. Can only be provided if `cumulative` is `True` or `frame` is provided.
- `cumulative` (optional): optional argument (default `False`) that can only be `True` if the `by` argument is provided. If `True`, then instead of returning the sum of all of the data in the context, returns the cumulative sum of all rows up to and including the current row when sorted according to the keys in the `by` argument. This argument cannot be provided if `frame` is also provided.
- `frame` (optional): optional argument that, if provided, must be a tuple of two values `(lower, upper)`, where each value is either an integer literal or `None`. This argument can only be provided if the `by` argument is also provided. If provided, it means the relative sum is performed on a subset of the selected records based on the values of `lower` and `upper` when sorted according to the keys in the `by` argument:
   - If `lower` is `None`, then all of the records from the beginning until the records specified by `upper` are included.
   - If `upper` is `None`, then all of the records from the records specified by `lower` until the end are included.
   - If `lower` and `upper` are integers, these integers specify which record they refer to, relative to the current record:
      - `-n`: `n` **BEFORE** the current record.
      - `0`: the current record.
      - `+n`: `n` **AFTER** the current record.
   - For example, `frame=(-10, 3)` would take the sum of the value from the current record, the 10 before it, and the 3 after it.

#### **Examples**
```
# Finds, for each customer's orders, the sum of the total price of that
# order and the two most recent orders before it.
Customers.orders.CALCULATE(sliding_sum=RELSUM(total_price, by=order_date.ASC(), per="Customers", frame=(-2, 0)))

# Finds the ratio between each customer's account balance and the global
# sum of all customers' account balances.
Customers.CALCULATE(ratio=acctbal / RELSUM(acctbal))

# Finds the ratio between each customer's account balance and the sum of all
# all customers' account balances within that nation.
Nations.customers.CALCULATE(ratio=acctbal / RELSUM(acctbal, per="Nations"))
```

### **RELAVG:**

The `RELAVG` function calculates the average of multiple rows of a singular expression within the same collection, e.g., the global average across all rows, or the average of rows per an ancestor of a sub-collection. The arguments:

#### **Parameters:**
- `expression`: the singular expression to average across multiple rows.
- `per` (optional): optional argument (default `None`) for the same `per` parameter as other window functions.
- `by` (optional): one or more collation values, as a single expression or an iterable, to order records in the current context. Required if `cumulative` is `True` or `frame` is provided.
- `cumulative` (optional): optional argument (default `False`). When `True` (requires `by`), returns the cumulative average up to the current row based on `by` order. Cannot be used with `frame`.
- `frame` (optional): a tuple `(lower, upper)` defining a subset of records for calculating the average, relative to the current row and ordered by `by`:
   - `lower=None`: includes all records from the start up to `upper`.
   - `upper=None`: includes all records from `lower` to the end.
   - Integer values in `lower` and `upper` are relative offsets:
      - `-n`: `n` rows **BEFORE** the current record.
      - `0`: the current record.
      - `+n`: `n` rows **AFTER** the current record.
   - For example, `frame=(1, None)` averages all rows after the current one.

#### **Examples**
```
# For each order, finds the average of the total price of that order and the 5Add commentMore actions
# orders before/after it when sorted by order date (breaking ties by the order
# key).
Orders.CALCULATE(window_average=RELAVG(total_price, by=(order_date.ASC(), key.ASC()), frame=(-5, 5)))

# Finds all customers whose account balance is above the global average of all
# customers' account balances.
Customers.WHERE(acctbal > RELAVG(acctbal))

# Finds all customers whose account balance is above the average of all
# customers' account balances within that nation.
Nations.customers.WHERE(acctbal > RELAVG(acctbal, per="Nations"))
```

### **RELCOUNT:**

The `RELCOUNT` function returns the number of non-null records in multiple rows of a singular expression within the same collection, e.g., the count of all non-null rows, or the count per an ancestor of a sub-collection. The arguments:

#### **Parameters:**
- `expression`: the singular expression to count the number of non-null entries across multiple rows.
- `per` (optional): optional argument (default `None`) for the same `per` parameter as other window functions.
- `by` (optional): one or more collation values, as a single expression or an iterable, to order records in the current context. Required if `cumulative` is `True` or `frame` is provided.
- `cumulative` (optional): optional argument (default `False`). When `True` (requires `by`), returns the cumulative count up to the current row based on `by` order. Cannot be used with `frame`.
- `frame` (optional): a tuple `(lower, upper)` defining a subset of records for counting, relative to the current row and ordered by `by`:
   - `lower=None`: includes all records from the start up to `upper`.
   - `upper=None`: includes all records from `lower` to the end.
   - Integer values in `lower` and `upper` are relative offsets:
      - `-n`: `n` rows **BEFORE** the current record.
      - `0`: the current record.
      - `+n`: `n` rows **AFTER** the current record.
   - For example, `frame=(None, 0)` counts all rows before and including the current record (similar to `cumulative=True`).


#### **Examples**
```
# Same as previous example, but using frames to exclude the current record
# instead of subtracting (acctbal >= 0)
Customers.CALCULATE(n_poorer_non_debt=RELCOUNT(KEEP_IF(acctbal, acctbal >= 0), by=(acctbal.ASC()), frame=(None, -1)))

# Divides each customer's account balance by the total number of positive
# account balances globally.
Customers.CALCULATE(ratio = acctbal / RELCOUNT(KEEP_IF(acctbal, acctbal > 0.0)))

# Divides each customer's account balance by the total number of positive
# account balances in the same nation.
Nations.customers.CALCULATE(ratio = acctbal / RELCOUNT(KEEP_IF(acctbal, acctbal > 0.0), per="Nations"))
```

### **RELSIZE:**

The `RELSIZE` function returns the total number of records, either globally or the count of sub-collection records per some ancestor collection. The arguments:

#### **Parameters:**
- `per` (optional): optional argument (default `None`) for the same `per` parameter as other window functions.
- `by` (optional): one or more collation values, as a single expression or an iterable, to order records in the current context. Required if `cumulative` is `True` or `frame` is provided.
- `cumulative` (optional): optional argument (default `False`). When `True` (requires `by`), returns the cumulative count of records up to the current row based on `by` order. Cannot be used with `frame`.
- `frame` (optional): a tuple `(lower, upper)` defining a subset of records for counting, relative to the current row and ordered by `by`:
   - `lower=None`: includes all records from the start up to `upper`.
   - `upper=None`: includes all records from `lower` to the end.
   - Integer values in `lower` and `upper` are relative offsets:
      - `-n`: `n` rows **BEFORE** the current record.
      - `0`: the current record.
      - `+n`: `n` rows **AFTER** the current record.
   - For example, `frame=(-10, -1)` counts up to 10 records before the current one, excluding the current record.


#### **Examples**
```
# For each customer's orders, count how many orders the customer made AFTER the
# current order.
Customers.orders.CALCULATE(n_orders_after=RELSIZE(by=(order_date.ASC(), key.ASC()), frame=(1, None)))

# Divides each customer's account balance by the number of total customers.
Customers.CALCULATE(ratio = acctbal / RELSIZE())

# Divides each customer's account balance by the number of total customers in
# that nation.
Nations.customers.CALCULATE(ratio = acctbal / RELSIZE(per="Nations"))
```
### PREV

The `PREV` function returns the value of an expression from a preceding record in the collection. The arguments:

#### **Parameters:**
- `expression`: the expression to return the shifted value of.
- `n` (optional): optional argument (default `1`) how many records backwards to look.
- `default` (optional): optional argument (default `None`) the value to output when there is no record `n` before the current record. This must be a valid literal.
- `by`: 1+ collation values, either as a single expression or an iterable of expressions, used to order the records of the current context.
- `per` (optional): optional argument (default `None`) for the same `per` argument as all other window functions.

#### **Examples**
```
# Find the 10 customers with at least 5 orders with the largest average time
# gap between their orders, in days.
order_info = orders.CALCULATE(
   day_diff=DATEDIFF("days", PREV(order_date, by=order_date.ASC(), per="Customers"), order_date)
)
Customers.WHERE(COUNT(orders) > 5).CALCULATE(
   name,
   average_order_gap=AVG(order_info.day_diff)
).TOP_K(10, by=average_order_gap.DESC())

# For every year/month, calculate the percent change in the number of
# orders made in that month from the previous month.
PARTITION(
   Orders(year=YEAR(order_date), month=MONTH(order_date)),
   name="orders",
   by=(year, month)
).CALCULATE(
   year,
   month,
   n_orders=COUNT(orders),
   pct_change=
      100.0
      * (COUNT(orders) - PREV(COUNT(orders), by=(year.ASC(), month.ASC())))
      / PREV(COUNT(orders), by=(year.ASC(), month.ASC()))
)
```

### NEXT

The `NEXT` function returns the value of an expression from a following record in the collection. In other words, `NEXT(expr, n)` is the same as `PREV(expr, -n)`. The arguments:

#### **Parameters:**
- `expression`: the expression to return the shifted value of.
- `n` (optional): optional argument (default `1`) how many records forward to look.
- `default` (optional): optional argument (default `None`) the value to output when there is no record `n` after the current record. This must be a valid literal.
- `by`: 1+ collation values, either as a single expression or an iterable of expressions, used to order the records of the current context.
- `per` (optional): optional argument (default `None`) for the same `per` argument as all other window functions.

## **9. CONTEXTLESS EXPRESSIONS**   

### **Purpose**
Reusable code snippets.  

### **Example**
Define and reuse filters:  
  ``` 
  is_high_value = package_cost > 1000  
  high_value_packages = Packages.WHERE(is_high_value)
  ```

## **10. SINGULAR**
### **Purpose**
SINGULAR in PyDough ensures data is explicitly treated as singular in sub-collection contexts, preventing undefined behavior if used correctly.

### **Examples**
```
region_order_values_1996 = regions.WHERE(
  HAS(nations.customers.orders) == 1
).CALCULATE(
    region_name=name,
    total_order_value=SUM(nations.customers.orders.WHERE(YEAR(order_date) == 1996).total_price)
).TOP_K(1, by=total_order_value.DESC())

region_order_values_1997 = regions.WHERE(
  HAS(nations.customers.orders) == 1
).CALCULATE(
    region_name=name,
    total_order_value=SUM(nations.customers.orders.WHERE(YEAR(order_date) == 1997).total_price)
).TOP_K(1, by=total_order_value.DESC())

result = EXAMPLE_GRAPH.CALCULATE(
    year_1996=region_order_values_1996.SINGULAR().total_order_value,
    year_1997=region_order_values_1997.SINGULAR().total_order_value
)
```

**Good Example #1**: Access the package cost of the most recent package ordered by each person. This is valid because even though `.packages` is plural with regards to `People`, the filter done will ensure that there is only one record for each record of `People`, so `.SINGULAR()` is valid. 

```
most_recent_package = packages.WHERE(
    RANKING(by=order_date.DESC(), levels=1) == 1
).SINGULAR()
People.CALCULATE(
    ssn,
    first_name,
    middle_name,
    last_name,
    most_recent_package_cost=most_recent_package.package_cost
)
```

**Good Example #2**: Access the email of the current occupant of each address that has the name `"John Smith"` (no middle name). This is valid if it is safe to assume that each address only has one current occupant named `"John Smith"` without a middle name.

```
js = current_occupants.WHERE(
    (first_name == "John") &  
    (last_name == "Smith") & 
    (HASNOT(middle_name) == 1)
).SINGULAR()
Addresses.CALCULATE(
    address_id,
    john_smith_email=DEFAULT_TO(js.email, "NO JOHN SMITH LIVING HERE")
)
```

**Bad Example #1**: This is invalid primarily because of two reasons:
1. Each `Addresses` might have multiple `current_occupants` named `John`, therefore the use of `.SINGULAR()`, though it would not raise an exception, is invalid.
2. Even if, `current_occupants` were non-plural after using `SINGULAR`, `packages` is a plural sub-collection of `current_occupants`, therefore, the data being accessed would be plural with regards to `Addresses`.
```
Addresses.CALCULATE(
    package_id=current_occupants.WHERE(
        first_name == "John"
    ).SINGULAR().packages.package_id
)
```
## **BINARY OPERATORS**

### **Arithmetic**

*   Operators: +, -, \*, /, \*\* (addition, subtraction, multiplication, division, exponentiation).
    
*   Example:Lineitems(value = (extended\_price \* (1 - (discount \*\* 2)) + 1.0) / part.retail\_price)
    
*   Warning: Division by 0 behavior depends on the database.
    

### **Comparisons**

*   Operators: <=, <, ==, !=, >, >=.
    
*   Example:Customers(in\_debt = acctbal < 0, is\_european = nation.region.name == "EUROPE")
    
*   Warning: Avoid chained inequalities (e.g., a <= b <= c). Use (a <= b) & (b <= c) or MONOTONIC.
    

### **Logical**

*   Operators: & (AND), | (OR), ~ (NOT).
    
*   Example:Customers(is\_eurasian = (nation.region.name == "ASIA") | (nation.region.name == "EUROPE"))
    
*   Warning: Use &, |, ~ instead of Python’s and, or, not.
    

## **UNARY OPERATORS****Negation**

*   Operator: - (flips sign).
    
*   Example:Lineitems(lost\_value = extended\_price \* (-discount))
    

## **OTHER OPERATORS**

### **Slicing**

#### Syntax
string\[start:stop:step\].
    
#### Example
Customers(country\_code = phone\[:3\])
    
#### Rules
- Step must be 1 or omitted; start/stop non-negative or omitted.
    

## **STRING FUNCTIONS**

*   LOWER(s): Converts string to lowercase.Example: LOWER(name) → "apple".
    
*   UPPER(s): Converts string to uppercase.Example: UPPER(name) → "APPLE".
    
*   LENGTH(s): Returns character count.Example: LENGTH(comment) → 42.
    
*   STARTSWITH(s, prefix): Checks prefix match.Example: STARTSWITH(name, "yellow") → True/False.
    
*   ENDSWITH(s, suffix): Checks suffix match.Example: ENDSWITH(name, "chocolate") → True/False.
    
*   CONTAINS(s, substr): Checks substring presence.Example: CONTAINS(name, "green") → True/False.
    
*   LIKE(s, pattern): SQL-style pattern matching (%, \_).Example: LIKE(comment, "%special%") → True/False.
    
*   JOIN\_STRINGS(delim, s1, s2, ...): Joins strings with a delimiter.Example: JOIN\_STRINGS("-", "A", "B") → "A-B".
    

## **DATETIME FUNCTIONS**

### YEAR

Calling `YEAR` on a date/timestamp extracts the year it belongs to:

```
Orders.WHERE(YEAR(order_date) == 1995)
```

### QUARTER

Calling `QUARTER` on a date/timestamp extracts the quarter of the year it belongs to. The range of output is from 1-4. Months 1-3 are part of quarter 1, months 4-6 are part of quarter 2, months 7-9 are part of quarter 3, and months 10-12 are part of quarter 4.

```
Orders.WHERE(QUARTER(order_date) == 1)
```

### MONTH

Calling `MONTH` on a date/timestamp extracts the month of the year it belongs to:

```
Orders.CALCULATE(is_summer = (MONTH(order_date) >= 6) & (MONTH(order_date) <= 8))
```

### DAY

Calling `DAY` on a date/timestamp extracts the day of the month it belongs to:

```
Orders.CALCULATE(is_first_of_month = DAY(order_date) == 1)
```

### HOUR

Calling `HOUR` on a date/timestamp extracts the hour it belongs to. The range of output
is from 0-23:

```
Orders.CALCULATE(is_12pm = HOUR(order_date) == 12)
```

### MINUTE

Calling `MINUTE` on a date/timestamp extracts the minute. The range of output
is from 0-59:

```
Orders.CALCULATE(is_half_hour = MINUTE(order_date) == 30)
```

### SECOND

Calling `SECOND` on a date/timestamp extracts the second. The range of output
is from 0-59:
```
Orders.CALCULATE(is_lt_30_seconds = SECOND(order_date) < 30)
```

* DATETIME: The DATETIME function is used to build/augment date/timestamp values. The first argument is the base date/timestamp, and it can optionally take in a variable number of modifier arguments.
  
    - The base argument can be one of the following: A string literal indicating that the current timestamp should be built, which has to be one of the following: `now`, `current_date`, `current_timestamp`, `current date`, `current timestamp`. All of these aliases are equivalent, case-insensitive, and ignore leading/trailing whitespace.
    - A column of datetime data.

  The modifier arguments can be the following (all of the options are case-insensitive and ignore leading/trailing/extra whitespace):

  - A string literal in the format `start of <UNIT>` indicating to truncate the datetime value to a certain unit, which can be the following:
   - **Years**: Supported aliases are `"years"`, `"year"`, and `"y"`.
   - **Quarters**: Supported aliases are `"quarters"`, `"quarter"`, and `"q"`.
   - **Months**: Supported aliases are `"months"`, `"month"`, and `"mm"`.
   - **Days**: Supported aliases are `"days"`, `"day"`, and `"d"`.
   - **Weeks**: Supported aliases are `"weeks"`, `"week"`, and `"w"`.
   - **Hours**: Supported aliases are `"hours"`, `"hour"`, and `"h"`.
   - **Minutes**: Supported aliases are `"minutes"`, `"minute"`, and `"m"`.
   - **Seconds**: Supported aliases are `"seconds"`, `"second"`, and `"s"`.

  - A string literal in the form `±<AMT> <UNIT>` indicating to add/subtract a date/time interval to the datetime value. The sign can be `+` or `-`, and if omitted the default is `+`. The amount must be an integer. The unit must be one of the same unit strings allowed for truncation. For example, "Days", "DAYS", and "d" are all treated the same due to case insensitivity.

  If there are multiple modifiers, they operate left-to-right.
  Usage examples:
  ``` 
  # Returns the following datetime moments:
  # 1. The current timestamp
  # 2. The start of the current month
  # 3. Exactly 12 hours from now
  # 4. The last day of the previous year
  # 5. The current day, at midnight
  # 6. The first day after the start of the current quarter
  # 7. The current week
  EXAMPLE_GRAPH.CALCULATE(
    ts_1=DATETIME('now'),
    ts_2=DATETIME('NoW', 'start of month'),
    ts_3=DATETIME(' CURRENT_DATE ', '12 hours'),
    ts_4=DATETIME('Current Timestamp', 'start of y', '- 1 D'),
    ts_5=DATETIME('NOW', '  Start  of  Day  '),
    ts_6=DATETIME('now', 'start of quarter', '+1 d'),
    ts_7=DATETIME('now', "start of week"),
  )

  # For each order, truncates the order date to the first day of the year
  Orders.CALCULATE(order_year=DATETIME(order_year, 'START OF Y'))
  
  # Get the orders made in the past 70 days
  orders_in_70_days= Orders.WHERE((DATEDIFF("days",date, 'now') <= 70))
  result= EXAMPLE_GRAPH.CALCULATE(total_orders=COUNT(orders_in_70_days))
  ```

* DATEDIFF: Calling DATEDIFF between 2 timestamps returns the difference in one of the following units of time: years, months, quarters, days, hours, minutes, or seconds.

  - `DATEDIFF("years", x, y)`: Returns the **number of full years since x that y occurred**. For example, if **x** is December 31, 2009, and **y** is January 1, 2010, it counts as **1 year apart**, even though they are only 1 day apart.
  - `DATEDIFF("quarters", x, y)`: Returns the **number of full quarters since x that y occurred**. For example, if **x** is March 31, 2014, and **y** is April 1, 2014, it counts as **1 quarter apart**, even though they are only 1 day apart.
  - `DATEDIFF("months", x, y)`: Returns the **number of full months since x that y occurred**. For example, if **x** is January 31, 2014, and **y** is February 1, 2014, it counts as **1 month apart**, even though they are only 1 day apart.
  - `DATEDIFF("weeks", x, y)`: Returns the **number of full weeks since x that y occurred**. The dates x and y are first truncated to the start of week (as specified by the `start_of_week` config), then the difference in number of full weeks is calculated (a week is defined as 7 days). For example, if `start_of_week` is set to Saturday:
    ```
    # If x is "2025-03-18" (Tuesday) and y is "2025-03-31" (Monday)
    DATEDIFF("weeks", x, y) returns 2
    ```
  - `DATEDIFF("days", x, y)`: Returns the **number of full days since x that y occurred**. For example, if **x** is 11:59 PM on one day, and **y** is 12:01 AM the next day, it counts as **1 day apart**, even though they are only 2 minutes apart.
  - `DATEDIFF("hours", x, y)`: Returns the **number of full hours since x that y occurred**. For example, if **x** is 6:59 PM and **y** is 7:01 PM on the same day, it counts as **1 hour apart**, even though the difference is only 2 minutes.
  - `DATEDIFF("minutes", x, y)`: Returns the **number of full minutes since x that y occurred**. For example, if **x** is 7:00 PM and **y** is 7:01 PM, it counts as **1 minute apart**, even though the difference is exactly 60 seconds.
  - `DATEDIFF("seconds", x, y)`: Returns the **number of full seconds since x that y occurred**. For example, if **x** is at 7:00:01 PM and **y** is at 7:00:02 PM, it counts as **1 second apart**.

  - Example:
  ``` 
  # Calculates, for each order, the number of days since January 1st 1992
  # that the order was placed:
  Orders.CALCULATE( 
    days_since=DATEDIFF("days", "1992-01-01", order_date)
  )
  ```

* DAYOFWEEK:

  The `DAYOFWEEK` function returns the day of the week for a given date/timestamp. It takes a single argument, which is a date/timestamp, and returns an integer between 1 and 7. In other words, `DAYOFWEEK` returns which day of the week is the given date/timestamp, where the first day of the give date/timestamp is decided by the `start_of_week` config.

  ```
  # Returns the day of the week for the order date
  Orders.CALCULATE(day_of_week = DAYOFWEEK(order_date))
  ```

* DAYNAME:

  The `DAYNAME` function returns the name of the day of the week for a given date/timestamp. It takes a single argument, which is a date/timestamp, and returns a string, corresponding to the name of the day of the week. This returns one of the following: `"Monday"`, `"Tuesday"`, `"Wednesday"`, `"Thursday"`, `"Friday"`, `"Saturday"`, or `"Sunday"`.

  ```
  # Returns the name of the day of the week for the order date
  Orders.CALCULATE(day_name = DAYNAME(order_date))
  ```

## **CONDITIONAL FUNCTIONS**

*   IFF(cond, a, b): Returns a if cond is True, else b.Example: IFF(acctbal > 0, acctbal, 0).
    
*   ISIN(val, (x, y)): Checks membership in a list.Example: ISIN(size, (10, 11)) → True/False.
    
*   DEFAULT\_TO(a, b): Returns first non-null value.Example: DEFAULT\_TO(tax, 0).
    
    
*   KEEP\_IF(a, cond): Returns a if cond is True, else null.Example: KEEP\_IF(acctbal, acctbal > 0).
    
*   MONOTONIC(a, b, c): Checks ascending order.Example: MONOTONIC(5, part.size, 10) → True/False.
    

## **NUMERICAL FUNCTIONS**

*   ABS(x): Absolute value.Example: ABS(-5) → 5.
    
*   ROUND(x, decimals): Rounds to decimals places.Example: ROUND(3.1415, 2) → 3.14.
    
*   POWER(x, exponent): Raises x to a power.Example: POWER(3, 2) → 9.
    
*   SQRT(x): Square root of x.Example: SQRT(16) → 4.
    

## **GENERAL NOTES**

*   Use &, |, ~ for logical operations (not and, or, not).
    
*   For chained inequalities, use MONOTONIC or explicit comparisons.
    
*   Aggregation functions convert plural values (e.g., collections) to singular values.
    
## **12. EXAMPLE QUERIES**  

* **Top 5 States by Average Occupants:**  

  addr_info = Addresses.WHERE(
    HAS(current_occupants) == 1
  ).CALCULATE(n_occupants=COUNT(current_occupants))  
  average_occupants=PARTITION(addr_info, name="addrs", by=state).CALCULATE(  
      state=state,  
      avg_occupants=AVG(addrs.n_occupants)  
  ).TOP_K(5, by=avg_occupants.DESC())  

* **Monthly Trans-Coastal Shipments:**  

  west_coast = (\"CA\", \"OR\", \"WA\")  
  east_coast = (\"NY\", \"NJ\", \"MA\")  
  monthly_shipments= Packages.WHERE(  
      ISIN(customer.current_address.state, west_coast) &  
      ISIN(shipping_address.state, east_coast)  
  ).CALCULATE(  
      month=MONTH(order_date),  
      year=YEAR(order_date)  
  )

* **Calculates, for each order, the number of days since January 1st 1992**:
  
  Orders.CALCULATE( 
   days_since=DATEDIFF("days","1992-01-01", order_date)
  )

* **Filter Nations by Name**  
  *Goal: Find nations whose names start with \"A\".*  
  *Code:*  
  nations_startwith = nations.CALCULATE(n_name=name, n_comment=comment).WHERE(STARTSWITH(name, 'A'))  
  nations_like = nations.CALCULATE(n_name=name, n_comment=comment).WHERE(LIKE(name, 'A%'))  

* **Customers in Debt from Specific Region**  
  *Goal: Identify customers in debt (negative balance) with ≥5 orders, from \"AMERICA\" (excluding Brazil).*  
  *Code:*  
  customer_in_debt = customers.CALCULATE(customer_name = name).WHERE(  
      (acctbal < 0) &  
      (COUNT(orders) >= 5) &  
      (nation.region.name == "AMERICA") &  
      (nation.name != "BRAZIL")  
  )

* **For each order, truncates the order date to the first day of the year**:
  
  Orders.CALCULATE(order_year=DATETIME(order_year, 'START OF Y'))

* **Orders per Customer in 1998**  
  *Goal: Count orders per customer in 1998 and sort by activity.*  
  *Code:*  
  customer_order_counts = customers.WHERE(
    HAS(orders) == 1
  ).CALCULATE(  
      key=key, 
      name=name,  
      num_orders=COUNT(orders.WHERE(YEAR(order_date) == 1998))  
  ).ORDER_BY(num_orders.DESC())  

* **High-Value Customers in Asia**  
  *Goal: Find customers in Asia with total spending > $1000.*  
  *Code:*  
  high_value_customers_in_asia = customers.WHERE(
    HAS(orders) == 1
  ).CALCULATE(  
      customer_key=key, 
      customer_name=name,  
      total_spent=SUM(orders.total_price)  
  ).WHERE((total_spent > 1000) & (nation.region.name == "ASIA"))  

* **Top 5 Most Profitable Nations**  
  *Goal: Identify regions with highest revenue.*  
  *Code:*  
  selected_regions = nations.WHERE(
    HAS(customers.orders) == 1
  ).CALCULATE(  
      region_name=name,  
      Total_revenue=SUM(customers.orders.total_price)  
  ).TOP_K(5, Total_revenue.DESC())  

* **Inactive Customers**  
  *Goal: Find customers who never placed orders.*  
  *Code:*  
  customers_without_orders = customers.WHERE(HASNOT(orders)==1).CALCULATE(  
      customer_key=key,  
      customer_name=name  
  )  

* **Customer Activity by Nation**  
  *Goal: Track active/inactive customers per nation.*  
  *Code:*  
  cust_info = customers.CALCULATE(is_active=HAS(orders)==1)  
  nation_summary = nations.CALCULATE(  
      nation_name=name,  
      total_customers=COUNT(cust_info),  
      active_customers=SUM(cust_info.is_active),  
      inactive_customers=COUNT(cust_info) - SUM(cust_info.is_active)  
  ).ORDER_BY(total_customers.DESC())  

* **High Balance, Low Spending Customers**  
  *Goal: Find top 10% in balance but bottom 25% in orders.*  
  *Code:*  
  customers_in_low_percentiles = customers.WHERE(  
      (PERCENTILE(by=acctbal.DESC()) <= 10) &  
      (PERCENTILE(by=COUNT(orders.key).ASC()) <= 25)  
  )

* **For each year, identify the priority with the highest percentage of made in that year with that priority, listing the year, priority, and percentage. Sort the results by year.**
  ```
  # Step 1: Extract year and priority from orders
  order_info = orders.CALCULATE(
      year = YEAR(order_date),
      priority = order_priority
  )

  # Step 2: Group by year and priority to get counts
  year_priority_counts = order_info.PARTITION(name="year_priority", by=(year, priority)).CALCULATE(
      year = year,
      priority = priority,
      n_orders = COUNT(orders)
  )

  # Step 3: Group by year and calculate percentages for each priority within that year
  year_priority_percentages = year_priority_counts.PARTITION(name="year_group", by=year).year_priority.CALCULATE(
              year,
              highest_priority=priority,
              priority_pct=100.0 * n_orders / RELSUM(n_orders, per="year_group"),
          ).WHERE(RANKING(by=priority_pct.DESC(), per="year_group") == 1).ORDER_BY(year.ASC())
  ```
*  **What is the ticker symbol, month, average closing price, highest price, lowest price**
  ```
  price_info = DailyPrices.CALCULATE(month=JOIN_STRINGS("-", YEAR(date), LPAD(MONTH(date), 2, "0"))symbol=ticker.symbol,)
  ticker_months = price_info.PARTITION(name="months", by=(symbol, month))
  months = ticker_months.PARTITION(name="symbol", by=symbol).months
  month_stats = months.CALCULATE(
        avg_close=AVG(DailyPrices.close),
        max_high=MAX(DailyPrices.high),
        min_low=MIN(DailyPrices.low),
  )
  result= month_stats.CALCULATE(symbol,month,avg_close,max_high)
  ```

* **Counts how many part sizes have an above-average number of combinations of part types/containers.**
  ```
  combo_groups = Parts.PARTITION(name="groups", by=(size, part_type, container))
  size_groups = combo_groups.PARTITION(name="sizes", by=size).CALCULATE(n_combos=COUNT(groups))
  EXAMPLE_GRAPH.CALCULATE(avg_n_combo=AVG(size_groups.n_combos)).CALCULATE(
        n_sizes=COUNT(size_groups.WHERE(n_combos > avg_n_combo)),
  )
  ```

* **Identify transactions that are below the average number of shares for transactions of the same combinations of (customer, stock, type), or the same combination of (customer, stock), or the same customer.**
  ```
  cust_tick_typ_groups = Transactions.PARTITION(name="ctt_groups", by=(customer_id, ticker_id, transaction_type)).CALCULATE(cus_tick_typ_avg_shares=AVG(Transactions.shares))
  cust_tick_groups = cust_tick_typ_groups.PARTITION(name="ct_groups", by=(customer_id, ticker_id)
  ).CALCULATE(cust_tick_avg_shares=AVG(ctt_groups.Transactions.shares))
  cus_groups = cust_tick_groups.PARTITION(name="c_groups", by=customer_id).CALCULATE(
      cust_avg_shares=AVG(ct_groups.ctt_groups.Transactions.shares)
  )
  cus_groups.ct_groups.ctt_groups.Transactions.WHERE(
            (shares < cus_tick_typ_avg_shares)
            & (shares < cust_tick_avg_shares)
            & (shares < cust_avg_shares)
        ).CALCULATE(
            transaction_id,
            customer.name,
            ticker.symbol,
            transaction_type,
            cus_tick_typ_avg_shares,
            cust_tick_avg_shares,
            cust_avg_shares,
        ).ORDER_BY(transaction_id.ASC())
  ```
  
## **GENERAL NOTES**

*   Use &, |, ~ for logical operations (not and, or, not).
    
*   For chained inequalities, use MONOTONIC or explicit comparisons.
    
*   Aggregation functions convert plural values (e.g., collections) to singular values.