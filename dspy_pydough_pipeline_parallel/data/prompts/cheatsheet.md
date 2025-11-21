<task_description>
You are an AI assistant tasked with converting natural language descriptions into PyDough code snippets. Your goal is to generate accurate and efficient PyDough code that can execute the requested database operations based on the provided natural language description. 

** SPECIAL INSTRUCTION: * Always be as deterministic as possible. Select the single most straightforward interpretation and implementation consistent with the provided context.

** SPECIAL INSTRUCTION: * Never introduce variations in logic, structure, or phrasing if a direct application of the rules yields a valid result. 

** IMPORTANT RULES: *
  - The high level collection must be called only once. Look at this BAD example, where you access the high level collection and then within the NDISTINCT use the GRAPH again, when you are already at that level. Bad Example `d93_ib_info = GRAPH.CALCULATE(count_total_d93_ib=NDISTINCT(GRAPH.install_bases.WHERE(install_bases.product.engineering_project_code == 'D83').serial_number))`

  -  When you access a collection, you CANNOT access it again because you are already at that level. Look at this BAD example, where you access install_bases and then within the WHERE use intall_bases again, when you are already at that level. Bad Example: `num_distinct_install_bases = NDISTINCT(install_bases.WHERE((install_bases.product.engineering_project_code == 'D83').serial_number)`.


THINK SILENTLY
</task_description>


<instructions>
To generate the PyDough code snippet, follow these steps:

1. Carefully analyze the provided natural language description to identify the database query or manipulation required. Extract the main components, such as collections, fields, and operations.

2. Generate PyDough code that:
   - Uses clear and concise syntax, adhering to the correct functions, parameters, and structure outlined in the PyDough Reference File.
   - Avoids the bad examples referenced in the PyDough Reference File.
   - Properly references fields and tables as defined in the Database Structure Reference File.
   - Includes comments for any complex operations, where necessary.
   - Assigns the final query to a variable.
   - Ensures proper indentation.
   - Follows the rules for using contextless expressions properly.
   - Adheres to the syntax and structure outlined in the PyDough Reference File.
   - Compares values using the equality operator (==) when necessary.
   - Ensures variable names are different from the field names in the Database Structure Reference File.
   - Ensure you start with the appropriate collection.
   - Returns only the exact data requested, without adding additional fields or information.
   - If you need to use the high-level top collection, use the appropriate name as defined in the Database Structure Reference File.
   - Refer to the provided definitions to answer the query when it requires a specific definition. For example, if the query asks for 'total order value,' use the definition provided.
   - High level graph should be used only for operations like computing averages, totals, frequencies, sum, etc. Do not use it for any other purposes. Also, avoid starting with the high level graph unless you need to perform an global operation to the end of the query.
   - When comparing strings you must use case insensitive by using LOWER function, use this in comparations only.

3. Determine if PARTITION is necessary. If it is not required, explore alternative methods such as CALCULATE or aggregations to achieve the desired result. If PARTITION is truly needed, use it appropriately.
   
4. If the input description contains any ambiguity, respond with a request for clarification regarding the specific details.

5. Enclose the generated PyDough code in a Python code block and ALWAYS provide an explanation of the code, as shown in the examples.

6. Iterative Improvement: Try different methods if the first approach doesn't work.  

10. Verification & Validation: Check for inconsistencies, logical errors, or missing details.  
</instructions>

<examples>
Here's how we analyse and create Pydough queries:

Question: Top 5 States by Average Occupants:
Let's break down the task:

1. For each address, we need to identify how many current occupants it has
2. We need to partition the addresses by the state, and for each state calculate the average occupants
3. We need to select the top 5 states by this average

First, let me think about the relationships in the database:
- `Addresses` contains all addreses.

So to count occupants per all addresses, we need to:
1. Partition the addresses by region and calculate the average of occupants per state
2. Access the `Addresses` collection and count the number of occupants per address
3. Select the top 5

Answer: Now let's implement this:
  ```python 
  result= Addresses.PARTITION(name="addrs", by=state).CALCULATE(  
      state=state,  
      avg_occupants=AVG(Addresses.CALCULATE(n_occupants=COUNT(current_occupants)).current_occupants )  
  ).TOP_K(5, by=avg_occupants.DESC())
  ```

Question: Find the customers name who never placed orders.
Let's analyze this request:

We need to find the customers who have never placed orders. This means we need to:
1. Access the `customers` collection
2. Filter for customers who don't have any orders 
3. Return their names

From the database structure reference, we can see that:
- Each customer has an `orders` property which is a list of orders placed by that customer
- We need to check if this list is empty

To do this:
1. We can use the `HASNOT` function to check if a customer has no orders
2. We'll filter the customers using `WHERE(HASNOT(orders)==1)`
3. Then select just their names using `CALCULATE`
Answer: Here's the PyDough code I'll generate:

```python
customers_without_orders = customers.WHERE(HASNOT(orders)==1).CALCULATE(
    customer_name=name
)
```
This code:
1. Starts with the `customers` collection
2. Filters to only include customers where `HASNOT(orders)==1`, meaning they have no orders
3. Uses `CALCULATE` to return only the customer names

Question: What is the total order value in Brazil in 1992? Total order value is defined as the sum of extended_price * (1 - discount) Return the name and the total order value.
Let's analyze this request:

1. Find the total order value in Brazil in 1992
2. Return the nation name and the total order value

First, I need to understand what "total order value" means. From the provided definitions:
> total order value = sum of extended_price * (1 - discount)

Now, let's think about how to build this query:

1. Start with `nations` and filter for "BRAZIL"
2. From Brazil, access `customers`
3. From customers, access `orders`
4. Filter orders to only include those from 1992
5. From filtered orders, access `lines`
6. Calculate line_value as extended_price * (1 - discount)
7. Sum up these line_values to get the total order value for Brazil in 1992

From the database structure:
- Nations have a name field, so I can filter for "BRAZIL"
- Nations have customers, and customers have orders
- Orders have line items (lines) that have extended_price and discount

Let's create the PyDough code:
```python
brazil_total_order_value = nations.WHERE(name == "BRAZIL").CALCULATE(
    nation_name=name,
    total_order_value=SUM(
        customers.orders.WHERE(YEAR(order_date) == 1992).lines.CALCULATE(
            line_value=extended_price * (1 - discount)
        ).line_value
    )
)
```
Question: Which part brands have at least 1 part that is above the average retail price for parts of that brand, below the average retail price for all parts, and has a size below 3.

Let's break down this request:

1. For each part brand, find parts that are:
   a. Above the average retail price for that specific brand
   b. Below the average retail price for ALL parts
   c. Have a size below 3

2. Return the brands that have at least 1 part meeting all these criteria

First, I need to calculate:
- The average retail price for each brand
- The overall average retail price for all parts

Then I need to filter parts that meet all three criteria, and finally return the brands that have at least one such part.

Let's build this step by step:

1. Calculate the average retail price for all parts:

To do this, I need the high-level graph TPCH as defined in the Database Structure Reference File to obtain the overall average price:
```
global_info= TPCH.CALCULATE(
    overall_avg_price=AVG(parts.retail_price)
)
```
2. Calculate the average retail price per brand:
```
brand_avg_prices = global_info.parts.PARTITION(name="brands", by=brand).CALCULATE(
    brand_avg_price=AVG(parts.retail_price)
)
```
3. Now I need to combine these to find the parts that meet all criteria:
```
selected_parts = parts.WHERE(
        (retail_price > brand_avg_price)
        & (retail_price < overall_avg_price)
        & (size < 3)
)
selected_brands = brands.WHERE(HAS(selected_parts)==1)
```
4. Now, filter the results to include only the brand and order them by brand. 
```
result= selected_brands.CALCULATE(brand).ORDER_BY(brand.ASC()) 
```

Answer: Let's put it all together:
global_info= TPCH.CALCULATE(
    overall_avg_price=AVG(parts.retail_price)
)
brand_avg_prices = global_info.parts.PARTITION(name="brands", by=brand).CALCULATE(
    brand_avg_price=AVG(parts.retail_price)
)
selected_parts = parts.WHERE(
        (retail_price > brand_avg_price)
        & (retail_price < overall_avg_price)
        & (size < 3)
)
selected_brands = brand_avg_prices.WHERE(HAS(selected_parts)==1)
result= selected_brands.CALCULATE(brand).ORDER_BY(brand.ASC()) 

This code works as follows:
1. First, I calculate the `overall_avg_price` across all parts in the database
2. Then I partition the parts by `brand` to group them
3. For each brand, I calculate:
   - The average retail price for parts of that brand
4. I use `HAS()` with a `WHERE` clause to check if any parts meet all three conditions:
   - Price greater than the brand's average
   - Price less than the overall average
   - Size less than 3
5. Finally, I filter to include only brands and order the results in ascending order.

Question: How many customers placed an order in 1995?
Let's break down this problem:

1. We need to count how many customers placed an order in 1995.
2. This means we need to:
   - Access the customers who have orders
   - Filter for orders placed in 1995
   - Count the distinct customers

Let's look at the data model:
- `customers` have `orders`
- Each `order` has an `order_date` field

To solve this, I need to:
1. Find all customers who have at least one order in 1995
2. Count these customers

The query should:
1. Start with the `customers` collection
2. Filter customers to include only those who have at least one order with order_date in 1995
3. Count these customers

The rule in the PyDough reference says:

"You should use `HAS` function to verify the 1 to N relationship between tables, and you can identify them because the related subcollection has a plural name."

In our case, we have a 1 to N relationship between customers and orders. Let's use the HAS function as recommended:
```
result = TPCH.CALCULATE(
    num_customers_with_orders_in_1995=COUNT(customers.WHERE(
        HAS(orders.WHERE(YEAR(order_date) == 1995)) == 1
    ))
)
```
</examples>


## **PyDough Cheat Sheet**

### **General Rules**

* This is **not** SQL; do not assume SQL syntax or behavior.
* Use the `HAS` function to check for one-to-many relationships, which are indicated by plural subcollection names.
    * **Example**: To count orders per nation, use `nations.WHERE(HAS(customers.orders)==1).CALCULATE(nation_name=name, num_of_orders=COUNT(customers.orders.key))`.
* When performing calculations involving attributes from different child collections, you must first use `CALCULATE` to create a new variable within the child collection.
    * **Incorrect**: `SUM(orders.lines.extended_price * (1 - orders.lines.discount))`
    * **Correct**: `SUM(orders.lines.CALCULATE(total_value = extended_price * (1 - discount)).total_value)`
* To use an attribute from a previous collection, you must have already defined it using `CALCULATE`.
* For ranking within a `CALCULATE` function, use the `RANKING` method and then filter by the rank number.
* To check if a value exists, use `PRESENT`, `HAS`, or `HASNOT()`—never compare directly with None.
---

### **Function-Specific Rules**

#### **`CALCULATE`**

* The `CALCULATE` function requires a **singular expression**, not a collection. You cannot use functions that return a collection (like `TOP_K`) directly within `CALCULATE`.
* When working with plural (one-to-many) sub-collections, you **must** use an aggregation function (e.g., `SUM`, `COUNT`).

#### **`TOP_K` and `ORDER_BY`**

* Always use `TOP_K` instead of `ORDER_BY` to get the highest, lowest, or a specific number of records.
* The `by` parameter in these functions requires an **expression**, never a collection or subcollection.
    * **Incorrect**: `supp_group.TOP_K(3, total_sales.DESC(na_pos='last'))` because `total_sales` is a collection.
    * **Correct**: You must provide an expression to order by, such as an aggregated value.

#### **`PARTITION`**

* The `PARTITION` function must be used as a method and requires two parameters: `name` and `by`.
* The `by` parameter only accepts **expressions**. It does not support collections, subcollections, or new calculations. Any value needed must be calculated beforehand.
    * **Incorrect**: `nations.PARTITION(by=(name))`
    * **Incorrect**: `...PARTITION(..., by=nation.suppliers.TOP_K(3, by=SUM(lines.extended_price).DESC()))` because `TOP_K` returns a collection.

---

## **1. COLLECTIONS & SUB-COLLECTIONS**

### **Syntax**
Access collections and sub-collections using dot notation.

### **Examples**:
* `People` → Accesses all records in the 'People' collection.
* `People.current_address` → Accesses the current addresses linked to people.
* `Packages.customer` → Accesses the customers linked to packages.

---

## **2. CALCULATE EXPRESSIONS**

### **Purpose**
Use it to derive new fields, rename existing ones, or select specific fields.

### **Syntax**
`Collection.CALCULATE(new_field=expression, ...)`

### **Key Examples**

* **Create derived fields**:
    ```
    Packages.CALCULATE(
        customer_name=JOIN_STRINGS(' ', customer.first_name, customer.last_name),
        cost_per_unit=package_cost / quantity
    )
    ```

* **Use conditional logic and multi-step calculations**:
    ```
    People.CALCULATE(
        has_middle_name=PRESENT(middle_name),
        full_name_with_middle=JOIN_STRINGS(" ", first_name, middle_name, last_name),
        full_name_without_middle=JOIN_STRINGS(" ", first_name, last_name),
    ).CALCULATE(
        full_name=IFF(has_middle_name, full_name_with_middle, full_name_without_middle),
        email=email
    )
    ```

### **Rules**

* **Aggregation**: You must use aggregation functions (e.g., `SUM`, `COUNT`) when working with plural sub-collections (one-to-many relationships).
* **Field Availability**:
    * A new field defined in a `CALCULATE` is not available until the operation completes. To use a field you just created, you need to chain another `CALCULATE`.
    * Existing fields not included in the final `CALCULATE` can be referenced during the calculation but will not appear in the final output.
* **Arguments**: Positional arguments must always come before keyword arguments.

---

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

- Use `&` (AND), `|` (OR), `~` (NOT) instead of `and`, `or`, `not`.
- Avoid chained comparisons (e.g., replace `a < b < c` with `(a < b) & (b < c)`).

---

## **4. SORTING (ORDER_BY)**

### **Syntax**
.ORDER_BY(field.ASC()/DESC(), ...)

### **Parameters**

- `.ASC(na_pos='last')` → Sort ascending, nulls last.
- `.DESC(na_pos='first')` → Sort descending, nulls first.

### **Examples**

- **Alphabetical sort**:
  ```
  People.ORDER_BY(last_name.ASC(), first_name.ASC())
  ```

- **Most expensive packages first**:
  ```
  Packages.ORDER_BY(package_cost.DESC())
  ```

---

## **5. SORTING TOP_K(k, by=field.DESC())**

### **Purpose**
Select top `k` records.

### **Syntax**
.TOP_K(k, by=field.DESC())

### **Example**

- **Top 10 customers by orders count**:
  ```
  customers.TOP_K(10, by=COUNT(orders).DESC())
  ```

- **Top 10 customers by orders count (but also selecting only the name)**:
  ```
  customers.CALCULATE(cust_name=name).TOP_K(10, by=COUNT(orders).DESC())
  ```

### **Rules**
- The two parameters are obligatory.

---

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
- Aggregations Function does not support calling aggregations inside of aggregations
  
---

---

## **7. PARTITION**

### **Purpose**
Group records into logical partitions based on specified keys, enabling operations on these sub-groups.

### **Syntax**
`Collection.PARTITION(name='group_name', by=(key1, key2, ...))`

### **Rules**

* **Partition Keys in `CALCULATE`**: All fields used in the `by` parameter (e.g., `key1`, `key2`) must be present as scalar fields in the collection *before* the `PARTITION` operation. They must be made available via a preceding `CALCULATE` if they are derived or nested. When referencing these keys within a subsequent `CALCULATE` operation inside the partition, you refer to them directly by their name, not prefixed with the collection name.
* **Scalar Keys**: Partition keys must be scalar fields (single values) from the collection.
* **Aggregation for Plural Values**: When accessing plural sub-collections (one-to-many relationships) within a `CALCULATE` after a `PARTITION`, you **must** use aggregation functions (e.g., `SUM`, `COUNT`).
* **Accessing Partitioned Data**: After a `PARTITION` operation, to access the original collection's records within each partition, you typically re-access the collection using its name (e.g., `.Packages` after a `PARTITION` on `Packages`). This is essential for operations like `WHERE` or `CALCULATE` that need to operate on the individual records within each group.
* **Down-streaming**: Fields defined in an ancestor `CALCULATE` (either before the `PARTITION` or at the `GRAPH` level) are accessible within operations on the partitioned sub-collections.

### **Good Examples**

* **Group addresses by state and count occupants**:
    ```
    Addresses.PARTITION(name="states", by=(state)).CALCULATE(
        state,
        n_people=COUNT(Addresses.current_occupants)
    )
    ```
    **IMPORTANT**: Notice how `state` is used directly in `CALCULATE` because it's a `by` parameter.

* **Group packages by year/month**:
    ```
    package_info = Packages.CALCULATE(order_year=YEAR(order_date), order_month=MONTH(order_date))
    package_info.PARTITION(name='packs', by=(order_year, order_month))
    ```

* **For every year/month, find all packages that were below the average cost of all packages ordered in that year/month**: Notice how the version of `Packages` that is the sub-collection of the `months` can access `avg_package_cost`, which was defined by its ancestor (at the `PARTITION` level).
    ```
    package_info = Packages.CALCULATE(order_year=YEAR(order_date), order_month=MONTH(order_date))
    package_info.PARTITION(name="months", by=(order_year, order_month)).CALCULATE(
        avg_package_cost=AVG(Packages.package_cost)
    ).Packages.WHERE(
        package_cost < avg_package_cost
    )
    ```
    **IMPORTANT**: Notice how the collection is re-accessed with `.Packages` after the `PARTITION` to filter on individual package costs within each month group.

* **For every customer, find the percentage of all orders made by current occupants of that city/state made by that specific customer. Includes the first/last name of the person, the city/state they live in, and the percentage**: Notice how the version of `Addresses` that is the sub-collection of the `cities` can access `total_packages`, which was defined by its ancestor (at the `PARTITION` level), and how more variables can be defined with `CALCULATE`.
    ```
    Addresses.WHERE(
        HAS(current_occupants)==1
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

* **For every part of the market segment find the total quantity sold**: Notice that you need to access the lines collection again after performing the `PARTITION` in `part_totals_per_segment`. After applying `PARTITION`, it’s necessary to re-access the collection if you need data from the original collection.
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

* **Good Example #1: Find every unique state.**
    ```
    Addresses.PARTITION(name="states", by=state).CALCULATE(Addresses)
    ```

* **Good Example #2: For every city/state, count how many people live in that city/state.**
    ```
    Addresses.PARTITION(name="cities", by=(city, state)).CALCULATE(
        state,
        city,
        n_people=COUNT(Addresses.current_occupants)
    )
    ```

* **Good Example #3: Find the top 5 years with the most people born in that year who have yahoo email accounts, listing the year and the number of people.**
    ```
    yahoo_people = People.CALCULATE(
        birth_year=YEAR(birth_date)
    ).WHERE(ENDSWITH(email, "@yahoo.com"))
    yahoo_people.PARTITION(name="years", by=birth_year).CALCULATE(
        birth_year,
        n_people=COUNT(People)
    ).TOP_K(5, by=n_people.DESC())
    ```

* **Good Example #4: Identify the states whose current occupants account for at least 1% of all packages purchased. List the state and the percentage.** Notice how `total_packages` is down-streamed from the graph-level `CALCULATE`.
    ```
    GRAPH.CALCULATE(
        total_packages=COUNT(Packages)
    ).Addresses.WHERE(
        HAS(current_occupants.package) == 1
    ).PARTITION(name="states", by=state).CALCULATE(
        state,
        pct_of_packages=100.0 * COUNT(Addresses.current_occupants.package) / total_packages
    ).WHERE(pct_of_packages >= 1.0)
    ```

* **Good Example #5: Identify which months of the year have numbers of packages shipped in that month that are above the average for all months.**
    ```
    pack_info = Packages.CALCULATE(order_month=MONTH(order_date))
    month_info = pack_info.PARTITION(name="months", by=order_month).CALCULATE(
        n_packages=COUNT(Packages)
    )
    GRAPH.CALCULATE(
        avg_packages_per_month=AVG(month_info.n_packages)
    ).PARTITION(pack_info, name="months", by=order_month).CALCULATE(
        month=order_month, # Use the already calculated order_month from pack_info
    ).WHERE(COUNT(Packages) > avg_packages_per_month)
    ```

* **Good Example #6: Find the 10 most frequent combinations of the state that the person lives in and the first letter of that person's name.** Notice how `state` can be used as a partition key of `people_info` since it was made available via down-streaming.
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

* **Good Example #7: Same as good example #6, but written differently so it will include people without a current address (their state is listed as `"N/A"`).**
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

* **Good Example #8: Partition the current occupants of each address by their birth year and filter to include individuals born in years with at least 10,000 births. For each such person, list their first/last name and the state they live in.** This is valid because `state` was down-streamed to `people_info` before it was partitioned, so when `current_occupants` is accessed as a sub-collection of the `years`, it still has access to `state`.
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

* **Good Example #9: Find all packages that meet the following criteria: they were ordered in the last year that any package in the database was ordered, their cost was below the average of all packages ever ordered, and the state it was shipped to received at least 10,000 packages that year.**
    ```
    GRAPH.CALCULATE(
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

* **Good Example #10: For each state, finds the largest number of packages shipped to a single city in that state.** This is done by first partitioning the packages by the city/state of the shipping address, with the name `cities`, then partitioning the result again on `states` with the name `states`. The `states` partition collection is able to access the data from the first partition as a sub-collection with the name `cities`.
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

* **Invalid: Referencing non-partition key in `CALCULATE` without aggregation.** Invalid because the `email` property is referenced, which is not one of the partition keys, even though the data being partitioned does have an `email` property, and it's not aggregated.
    ```
    People.CALCULATE(birth_year=YEAR(birth_date)).PARTITION(name="years", by=birth_year).CALCULATE(
        birth_year,
        email,
        n_people=COUNT(People)
    )
    ```

* **Invalid: Using an expression directly as a partition key.** Invalid because `YEAR(order_date)` is not allowed to be used as a partition term directly; it must be calculated into a named field first.
    ```
    Packages.PARTITION(name="years", by=YEAR(order_date)).CALCULATE(
        n_packages=COUNT(Packages)
    )
    ```

* **Invalid: Using a nested field directly as a partition key.** Invalid because `current_address.state` is not allowed to be used as a partition term directly; it must be calculated into a named field first.
    ```
    People.PARTITION(name="state", by=current_address.state).CALCULATE(
        n_packages=COUNT(People)
    )
    ```

* **Invalid: Referencing a plural field without aggregation after partition.** Invalid because the `People.email` property is plural with regards to the `years` collection and thus cannot be referenced in a `CALCULATE` unless it is aggregated.
    ```
    People.CALCULATE(birth_year=YEAR(birth_date)).PARTITION(name="years", by=birth_year).CALCULATE(
        birth_year,
        People.email,
        n_people=COUNT(People)
    )
    ```

* **Bad Example #1: Invalid version of good example #6 due to uncalculated partition keys.** Invalid because `state` and `first_name[:1]` are not made available via a `CALCULATE` before being used as partition terms.
    ```
    Addresses.current_occupants.PARTITION(name="combinations", by=(state, first_name[:1])).CALCULATE(
        state,
        first_name[:1],
        n_people=COUNT(current_occupants),
    ).TOP_K(10, by=n_people.DESC())
    ```

* **Bad Example #2: Invalid because `email` is not a partition key and is not aggregated.** Invalid because the `email` property is referenced, which is not one of the partition keys, even though the data being partitioned does have an `email` property.
    ```
    People.CALCULATE(birth_year=YEAR(birth_date)).PARTITION(name="years", by=birth_year).CALCULATE(
        birth_year,
        email,
        n_people=COUNT(People)
    )
    ```

* **Bad Example #3: Incorrect collection access after `PARTITION`.** Invalid version of good example #6 that accesses the sub-collection of `combinations` with the wrong name `Addresses` instead of `current_occupants`.
    ```
    people_info = Addresses.CALCULATE(state).current_occupants.CALCULATE(
        first_letter=first_name[:1],
    )
    people_info.PARTITION(name="combinations", by=(state, first_letter)).CALCULATE(
        state,
        first_letter,
        n_people=COUNT(Addresses), # Incorrect collection access
    ).TOP_K(10, by=n_people.DESC())
    ```

---

## **8. WINDOW FUNCTIONS**

Window functions in PyDough operate on a "window" of records. This window can be the entire current collection, or a subset defined by an ancestor.

### **`per` Argument**

Window functions have an optional `per` argument.
* **Omitted `per`**: If omitted, the window function applies to all records of the current collection (e.g., rank all customers in the entire dataset).
* **Provided `per`**: If provided, it should be a string that describes which ancestor of the current context the window function should be calculated with regards to. In this case, the set of values used by the window function will be specific to each record of the corresponding ancestor (e.g., rank all customers *per-nation*).

### **Handling Ambiguous Ancestor Names**

If there are multiple ancestors of the current context with the same name, the `per` string should include a suffix `:idx` where `idx` specifies which ancestor with that name to use:
* `1`: Refers to the most recent ancestor with that name.
* `2`: Refers to the 2nd most recent ancestor with that name, and so on.

**Example of `per` with `:idx`:**

```
order_info = Orders.CALCULATE(y=YEAR(order_date), m=MONTH(order_date))
p1 = order_info.PARTITION(name="groups", by=(y, m))
p2 = p1.PARTITION(name="groups", by=(y)) # Corrected syntax for second PARTITION
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

---

### **8.1. RANKING**

Assigns a rank to each record within its window.

#### **Syntax**
`RANKING(by=field.DESC_OR_ASC(), per='collection_name', allow_ties=False, dense=False)`

#### **Parameters**

* `by`: Ordering criteria for ranking. Specify the field and order (e.g., `acctbal.DESC()`, `order_date.ASC()`).
* `per` (optional): Hierarchy level at which to perform the ranking (e.g., `per="nation"` for per-nation ranking). Must be an ancestor of the current context. Use `name:idx` for ambiguous ancestor names.
* `allow_ties` (default `False`): If `True`, records with the same value for the `by` field will receive the same rank.
* `dense` (default `False`): If `True`, tied ranks do not create gaps in the ranking sequence.

#### **Examples**

```
# Rank every customer relative to all other customers by acctbal
Regions.nations.customers.CALCULATE(r=RANKING(by=acctbal.DESC()))

# Rank every customer relative to other customers in the same nation, by acctbal
Regions.nations.customers.CALCULATE(r=RANKING(by=acctbal.DESC(), per="nations"))

# Rank every customer relative to other customers in the same region, by acctbal
Regions.nations.customers.CALCULATE(r=RANKING(by=acctbal.DESC(), per="Regions"))

# Rank customers per-nation by their account balance (highest = rank #1, no ties)
Nations.customers.CALCULATE(r = RANKING(by=acctbal.DESC(), per="Nations"))

# For every customer, finds their most recent order (ties allowed)
Customers.orders.WHERE(RANKING(by=order_date.DESC(), per="Customers", allow_ties=True) == 1)
```

---

### **8.2. PERCENTILE**

Calculates the percentile for each record within its window.

#### **Syntax**
`PERCENTILE(by=field.ASC_OR_DESC(), n_buckets=100, per="collection_name")`

#### **Parameters**

* `by`: Ordering criteria. Determines the order by which records are evaluated for percentile calculation.
* `n_buckets` (default `100`): The number of percentile buckets. For example, `100` creates percentiles (1-100), `1000` creates permilles (1-1000).
* `per` (optional): The same `per` argument as all other window functions. If omitted, the percentile is calculated across the entire current collection.

#### **Examples**

```
# Keep the top 0.1% of customers with the highest account balances.
Customers.WHERE(PERCENTILE(by=acctbal.ASC(), n_buckets=1000) == 1000)

# For every region, find the top 5% of customers with the highest account balances.
Regions.nations.customers.WHERE(PERCENTILE(by=acctbal.ASC(), per="Regions") > 95)
```

---

### **8.3. RELSUM**

The `RELSUM` function calculates the sum of a singular expression across multiple rows within the same collection. This can be a global sum or a sum per ancestor collection.

#### **Parameters:**

* `expression`: The singular expression whose values will be summed across multiple rows.
* `per` (optional): The ancestor hierarchy level at which to perform the sum (default `None`). See the general explanation of the `per` argument for window functions.
* `by` (optional): One or more collation values (a single expression or an iterable of expressions) used to order the records of the current context. This parameter is required if `cumulative` is `True` or `frame` is provided.
* `cumulative` (optional, default `False`): If `True`, the function returns the cumulative sum of all rows up to and including the current row, based on the ordering specified by the `by` argument. This argument can only be `True` if `by` is provided and cannot be provided if `frame` is also provided.
* `frame` (optional): A tuple `(lower, upper)` that defines a sliding window of records relative to the current record. This argument can only be provided if `by` is also provided. Each value in the tuple can be:
    * `None`:
        * If `lower` is `None`, includes all records from the beginning of the window up to `upper`.
        * If `upper` is `None`, includes all records from `lower` to the end of the window.
    * Integer literal: Specifies an offset relative to the current record:
        * `-n`: `n` records **BEFORE** the current record.
        * `0`: The current record.
        * `+n`: `n` records **AFTER** the current record.
    * Example: `frame=(-10, 3)` sums values from 10 records before the current, the current record, and 3 records after the current.

#### **Examples**

```
# Finds, for each customer's orders, the sum of the total price of that
# order and the two most recent orders before it.
Customers.orders.CALCULATE(sliding_sum=RELSUM(total_price, by=order_date.ASC(), per="Customers", frame=(-2, 0)))

# Finds the ratio between each customer's account balance and the global
# sum of all customers' account balances.
Customers.CALCULATE(ratio=acctbal / RELSUM(acctbal))

# Finds the ratio between each customer's account balance and the sum of all
# customers' account balances within that nation.
Nations.customers.CALCULATE(ratio=acctbal / RELSUM(acctbal, per="Nations"))
```

---

### **8.4. RELAVG**

The `RELAVG` function calculates the average of a singular expression across multiple rows within the same collection. This can be a global average or an average per ancestor collection.

#### **Parameters:**

* `expression`: The singular expression whose values will be averaged across multiple rows.
* `per` (optional): The ancestor hierarchy level at which to perform the average (default `None`). See the general explanation of the `per` argument for window functions.
* `by` (optional): One or more collation values (a single expression or an iterable) used to order records in the current context. This parameter is required if `cumulative` is `True` or `frame` is provided.
* `cumulative` (optional, default `False`): If `True`, the function returns the cumulative average of all rows up to the current row, based on the ordering specified by the `by` argument. This argument requires `by` to be provided and cannot be used with `frame`.
* `frame` (optional): A tuple `(lower, upper)` that defines a sliding window of records relative to the current record, ordered by `by`.
    * `None`:
        * If `lower` is `None`, includes all records from the start up to `upper`.
        * If `upper` is `None`, includes all records from `lower` to the end.
    * Integer values: Relative offsets:
        * `-n`: `n` rows **BEFORE** the current record.
        * `0`: The current record.
        * `+n`: `n` rows **AFTER** the current record.
    * Example: `frame=(1, None)` averages all rows after the current one.

#### **Examples**

```
# For each order, finds the average of the total price of that order and the 5
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

---

### **8.5. RELCOUNT**

The `RELCOUNT` function returns the number of non-null records for a singular expression across multiple rows within the same collection. This can be a global count or a count per ancestor collection.

#### **Parameters:**

* `expression`: The singular expression for which non-null entries will be counted across multiple rows.
* `per` (optional): The ancestor hierarchy level at which to perform the count (default `None`). See the general explanation of the `per` argument for window functions.
* `by` (optional): One or more collation values (a single expression or an iterable) used to order records in the current context. This parameter is required if `cumulative` is `True` or `frame` is provided.
* `cumulative` (optional, default `False`): If `True`, the function returns the cumulative count of non-null records up to the current row, based on the ordering specified by the `by` argument. This requires `by` and cannot be used with `frame`.
* `frame` (optional): A tuple `(lower, upper)` that defines a sliding window of records relative to the current record, ordered by `by`.
    * `None`:
        * If `lower` is `None`, includes all records from the start up to `upper`.
        * If `upper` is `None`, includes all records from `lower` to the end.
    * Integer values: Relative offsets:
        * `-n`: `n` rows **BEFORE** the current record.
        * `0`: The current record.
        * `+n`: `n` rows **AFTER** the current record.
    * Example: `frame=(None, 0)` counts all rows before and including the current record (similar to `cumulative=True`).

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

---

### **8.6. RELSIZE**

The `RELSIZE` function returns the total number of records within a defined window, either globally or per ancestor collection.

#### **Parameters:**

* `per` (optional): The ancestor hierarchy level at which to count records (default `None`). See the general explanation of the `per` argument for window functions.
* `by` (optional): One or more collation values (a single expression or an iterable) used to order records in the current context. This parameter is required if `cumulative` is `True` or `frame` is provided.
* `cumulative` (optional, default `False`): If `True`, the function returns the cumulative count of records up to the current row, based on the ordering specified by the `by` argument. This requires `by` and cannot be used with `frame`.
* `frame` (optional): A tuple `(lower, upper)` that defines a sliding window of records relative to the current record, ordered by `by`.
    * `None`:
        * If `lower` is `None`, includes all records from the start up to `upper`.
        * If `upper` is `None`, includes all records from `lower` to the end.
    * Integer values: Relative offsets:
        * `-n`: `n` rows **BEFORE** the current record.
        * `0`: The current record.
        * `+n`: `n` rows **AFTER** the current record.
    * Example: `frame=(-10, -1)` counts up to 10 records before the current one, excluding the current record.

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

---

### **8.7. PREV**

The `PREV` function returns the value of an expression from a preceding record within the current collection's window.

#### **Parameters:**

* `expression`: The expression whose value will be retrieved from a previous record.
* `n` (optional, default `1`): The number of records backward to look.
* `default` (optional, default `None`): The value to output when there is no record `n` before the current record (e.g., at the beginning of the window). This must be a valid literal.
* `by`: One or more collation values (a single expression or an iterable of expressions) used to order the records of the current context. This ordering determines which record is considered "previous."
* `per` (optional, default `None`): The ancestor hierarchy level at which to perform the operation. See the general explanation of the `per` argument for window functions.

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
    Orders.CALCULATE(year=YEAR(order_date), month=MONTH(order_date)), # Corrected syntax for CALCULATE inside PARTITION
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

---

### **8.8. NEXT**

The `NEXT` function returns the value of an expression from a following record within the current collection's window. Conceptually, `NEXT(expr, n)` is equivalent to `PREV(expr, -n)`.

#### **Parameters:**

* `expression`: The expression whose value will be retrieved from a following record.
* `n` (optional, default `1`): The number of records forward to look.
* `default` (optional, default `None`): The value to output when there is no record `n` after the current record (e.g., at the end of the window). This must be a valid literal.
* `by`: One or more collation values (a single expression or an iterable of expressions) used to order the records of the current context. This ordering determines which record is considered "next."
* `per` (optional, default `None`): The ancestor hierarchy level at which to perform the operation. See the general explanation of the `per` argument for window functions.

---

## **9. CONTEXTLESS EXPRESSIONS**

### **Purpose**
Contextless expressions are reusable code snippets that can define values or conditions, making your queries more readable and maintainable. They are evaluated in the context where they are used.

### **Example**
Define and reuse filters:
```
is_high_value = package_cost > 1000
high_value_packages = Packages.WHERE(is_high_value)
```

---

## **10. SINGULAR**

### **Purpose**
The `SINGULAR` function in PyDough is used to explicitly treat a collection as if it contains only a single record. This is crucial in contexts where a sub-collection might technically be plural but, due to filtering or other operations, is expected to yield only one record per parent record. Using `SINGULAR()` allows you to access fields of this "single" record directly. If the collection actually contains more than one record after `SINGULAR()` is applied, the behavior is undefined (it will typically pick an arbitrary record, but this is not guaranteed and should not be relied upon).

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

result = TPCH.CALCULATE(
    year_1996=region_order_values_1996.SINGULAR().total_order_value,
    year_1997=region_order_values_1997.SINGULAR().total_order_value
)
```

**Good Example #1**: Access the package cost of the most recent package ordered by each person. This is valid because even though `.packages` is plural with regards to `People`, the filter done via `RANKING` ensures that there is only one record selected for each `People` record, making `.SINGULAR()` valid.

```
most_recent_package = packages.WHERE(
    RANKING(by=order_date.DESC(), per="People", allow_ties=False) == 1 # Added 'per' and 'allow_ties' for clarity
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

**Bad Example #1**: This example is invalid for two reasons:
1. Each `Addresses` record might have multiple `current_occupants` named "John." Even though `.SINGULAR()` wouldn't raise an exception, its use is logically incorrect here as it doesn't guarantee a single record.
2. Even if `current_occupants` somehow became singular after filtering, `packages` is a plural sub-collection of `current_occupants`. Therefore, attempting to directly access `packages.package_id` without aggregation or further singling out would still result in plural data being returned for a singular context.

```
Addresses.CALCULATE(
    package_id=current_occupants.WHERE(
        first_name == "John"
    ).SINGULAR().packages.package_id # 'packages' is plural here
)
```

---

---

## **11. OPERATORS**

PyDough supports various operators for performing calculations, comparisons, and logical operations.

### **11.1. BINARY OPERATORS**

These operators work on two operands.

#### **Arithmetic Operators**

* **Operators**: `+` (addition), `-` (subtraction), `*` (multiplication), `/` (division), `**` (exponentiation).
* **Example**:
    ```
    Lineitems(value = (extended_price * (1 - (discount ** 2)) + 1.0) / part.retail_price)
    ```
* **Warning**: Behavior for division by zero (`/`) is dependent on the underlying database system.

#### **Comparison Operators**

* **Operators**: `<=`, `<`, `==`, `!=`, `>`, `>=` (less than or equal to, less than, equal to, not equal to, greater than, greater than or equal to).
* **Example**:
    ```
    Customers(in_debt = acctbal < 0, is_european = nation.region.name == "EUROPE")
    ```
* **Warning**: Avoid chained inequalities (e.g., `a <= b <= c`). Instead, use explicit logical `AND` (`(a <= b) & (b <= c)`) or consider using a `MONOTONIC` function if available for range checks.

#### **Logical Operators**

* **Operators**: `&` (logical AND), `|` (logical OR), `~` (logical NOT). These are crucial for combining conditions.
* **Example**:
    ```
    Customers(is_eurasian = (nation.region.name == "ASIA") | (nation.region.name == "EUROPE"))
    ```
* **Warning**: Always use PyDough's `&`, `|`, `~` for logical operations within expressions, not Python's built-in `and`, `or`, `not` keywords, which have different precedence and behavior in this context.

### **11.2. UNARY OPERATORS**

These operators work on a single operand.

#### **Negation**

* **Operator**: `-` (flips the sign of a numeric value).
* **Example**:
    ```
    Lineitems(lost_value = extended_price * (-discount))
    ```

---

### **11.3. OTHER OPERATORS**

#### **Slicing**

Used for extracting substrings from string fields.

* **Syntax**: `string[start:stop:step]`
* **Example**:
    ```
    Customers(country_code = phone[:3])
    ```
* **Rules**:
    * The `step` parameter must be `1` or omitted. Other `step` values are not supported.
    * `start` and `stop` values must be non-negative integers or omitted. Negative indices (like `[-1]`) are generally not supported for slicing in this context, use string functions if available for equivalent behavior.
    
---

## **12. STRING FUNCTIONS**

*   LOWER(s): Converts string to lowercase.Example: LOWER(name) → "apple".
    
*   UPPER(s): Converts string to uppercase.Example: UPPER(name) → "APPLE".
    
*   LENGTH(s): Returns character count.Example: LENGTH(comment) → 42.
    
*   STARTSWITH(s, prefix): Checks prefix match.Example: STARTSWITH(name, "yellow") → True/False.
    
*   ENDSWITH(s, suffix): Checks suffix match.Example: ENDSWITH(name, "chocolate") → True/False.
    
*   CONTAINS(s, substr): Checks substring presence.Example: CONTAINS(name, "green") → True/False.
    
*   LIKE(s, pattern): SQL-style pattern matching (%, \_).Example: LIKE(comment, "%special%") → True/False.
    
*   JOIN\_STRINGS(delim, s1, s2, ...): Joins strings with a delimiter.Example: JOIN\_STRINGS("-", "A", "B") → "A-B".

---

## **13. DATETIME FUNCTIONS**

*   YEAR(dt): Extracts year.Example: YEAR(order\_date) == 1995.
    
*   MONTH(dt): Extracts month (1-12).Example: MONTH(order\_date) >= 6.
    
*   DAY(dt): Extracts day (1-31).Example: DAY(order\_date) == 1.
    
*   HOUR(dt): Extracts hour (0-23).Example: HOUR(order\_date) == 12.
    
*   MINUTE(dt): Extracts minute (0-59).Example: MINUTE(order\_date) == 30.
    
*   SECOND(dt): Extracts second (0-59).Example: SECOND(order\_date) < 30.

* DATETIME: The DATETIME function is used to build/augment date/timestamp values. The first argument is the base date/timestamp, and it can optionally take in a variable number of modifier arguments.
  
    - The base argument can be one of the following: A string literal indicating that the current timestamp should be built, which has to be one of the following: `now`, `current_date`, `current_timestamp`, `current date`, `current timestamp`. All of these aliases are equivalent, case-insensitive, and ignore leading/trailing whitespace.
    - A column of datetime data.

  The modifier arguments can be the following (all of the options are case-insensitive and ignore leading/trailing/extra whitespace):

  - A string literal in the format `start of <UNIT>` indicating to truncate the datetime value to a certain unit, which can be the following:
   - **Years**: Supported aliases are `"years"`, `"year"`, and `"y"`.
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
  TPCH.CALCULATE(
    ts_1=DATETIME('now'),
    ts_2=DATETIME('NoW', 'start of month'),
    ts_3=DATETIME(' CURRENT_DATE ', '12 hours'),
    ts_4=DATETIME('Current Timestamp', 'start of y', '- 1 D'),
    ts_5=DATETIME('NOW', '  Start  of  Day  '),
  )

  # For each order, truncates the order date to the first day of the year
  Orders.CALCULATE(order_year=DATETIME(order_year, 'START OF Y'))

  # Get the orders made in the past 70 days
  orders_in_70_days= Orders.WHERE((DATEDIFF("days",date, 'now') <= 70))
  result= TPCH.CALCULATE(total_orders=COUNT(orders_in_70_days))
  ```

* DATEDIFF: Calling DATEDIFF between 2 timestamps returns the difference in one of the following units of time:     years, months, days, hours, minutes, or seconds.

  - `DATEDIFF("years", x, y)`: Returns the **number of full years since x that y occurred**. For example, if **x** is December 31, 2009, and **y** is January 1, 2010, it counts as **1 year apart**, even though they are only 1 day apart.
  - `DATEDIFF("months", x, y)`: Returns the **number of full months since x that y occurred**. For example, if **x** is January 31, 2014, and **y** is February 1, 2014, it counts as **1 month apart**, even though they are only 1 day apart.
  - `DATEDIFF("weeks", x, y)`: Returns the **number of full weeks since x that y occurred**. The dates x and y are first truncated to the start of week (as specified by the `start_of_week` config), then the difference in number of full weeks is calculated (a week is defined as 7 days). For example, if `start_of_week` is set to Saturday:
    ```python
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

  The `DAYOFWEEK` function returns the day of the week for a given date/timestamp. It takes a single argument, which is a date/timestamp, and returns an integer between 0 and 6. In other words, `DAYOFWEEK` returns which day of the week is the given date/timestamp, where the first day of the give date/timestamp is decided by the `start_of_week` config. The `start_of_week` is Monday, represented by 0.

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

---

## **14. CONDITIONAL FUNCTIONS**

These functions allow you to introduce conditional logic into your expressions.

* `IFF(cond, a, b)`: Returns `a` if `cond` evaluates to `True`, otherwise returns `b`.
    * **Example**: `IFF(acctbal > 0, acctbal, 0)` (Returns account balance if positive, else 0).

* `ISIN(val, (x, y, ...))` : Checks if `val` is a member of the provided list of values `(x, y, ...)`. Returns `True` or `False`.
    * **Example**: `ISIN(size, (10, 11))` (Checks if 'size' is 10 or 11).

* `DEFAULT_TO(a, b)`: Returns the first non-null value among the arguments. If `a` is null, returns `b`.
    * **Example**: `DEFAULT_TO(tax, 0)` (Uses 'tax' value if available, otherwise defaults to 0).

* `KEEP_IF(a, cond)`: Returns `a` if `cond` is `True`, otherwise returns `NULL`.
    * **Example**: `KEEP_IF(acctbal, acctbal > 0)` (Returns account balance only if it's positive, else null).

* `MONOTONIC(a, b, c)`: Checks if the values `a`, `b`, and `c` are in strictly ascending order (i.e., `a < b < c`). Returns `True` or `False`. Can be used with more than three arguments to check monotonic increasing sequence.
    * **Example**: `MONOTONIC(5, part.size, 10)` (Checks if 5 < part.size < 10).

---

## **15. NUMERICAL FUNCTIONS**

Functions for performing common mathematical operations.

* `ABS(x)`: Returns the absolute value of `x`.
    * **Example**: `ABS(-5)` → `5`.

* `ROUND(x, decimals)`: Rounds `x` to the specified number of `decimals` places.
    * **Example**: `ROUND(3.1415, 2)` → `3.14`.

* `POWER(x, exponent)`: Raises `x` to the power of `exponent`.
    * **Example**: `POWER(3, 2)` → `9` (3 squared).

* `SQRT(x)`: Returns the square root of `x`.
    * **Example**: `SQRT(16)` → `4`.

---

## **16. EXAMPLE QUERIES**

These examples demonstrate how to combine PyDough syntax elements to perform various data analysis tasks.

* **Monthly Trans-Coastal Shipments:**
    ```
    west_coast = ("CA", "OR", "WA")
    east_coast = ("NY", "NJ", "MA")
    monthly_shipments= Packages.WHERE(
        ISIN(customer.current_address.state, west_coast) &
        ISIN(shipping_address.state, east_coast)
    ).CALCULATE(
        month=MONTH(order_date),
        year=YEAR(order_date)
    )
    ```

* **Calculates, for each order, the number of days since January 1st 1992**:
    ```
    Orders.CALCULATE(
        days_since=DATEDIFF("days","1992-01-01", order_date)
    )
    ```

* **Filter Nations by Name**
    *Goal: Find nations whose names start with "A".*
    *Code:*
    ```
    nations_startwith = nations.CALCULATE(n_name=name, n_comment=comment).WHERE(STARTSWITH(name, 'A'))
    nations_like = nations.CALCULATE(n_name=name, n_comment=comment).WHERE(LIKE(name, 'A%'))
    ```

* **Customers in Debt from Specific Region**
    *Goal: Identify customers in debt (negative balance) with ≥5 orders, from "AMERICA" (excluding Brazil).*
    *Code:*
    ```
    customer_in_debt = customers.CALCULATE(customer_name = name).WHERE(
        (acctbal < 0) &
        (COUNT(orders) >= 5) &
        (nation.region.name == "AMERICA") &
        (nation.name != "BRAZIL")
    )
    ```

* **For each order, truncates the order date to the first day of the year**:
    ```
    Orders.CALCULATE(order_year=DATETIME(order_year, 'START OF Y'))
    ```

* **Orders per Customer in 1998**
    *Goal: Count orders per customer in 1998 and sort by activity.*
    *Code:*
    ```
    customer_order_counts = customers.WHERE(
        HAS(orders) == 1
    ).CALCULATE(
        key=key,
        name=name,
        num_orders=COUNT(orders.WHERE(YEAR(order_date) == 1998))
    ).ORDER_BY(num_orders.DESC())
    ```

* **High-Value Customers in Asia**
    *Goal: Find customers in Asia with total spending > $1000.*
    *Code:*
    ```
    high_value_customers_in_asia = customers.WHERE(
        HAS(orders) == 1
    ).CALCULATE(
        customer_key=key,
        customer_name=name,
        total_spent=SUM(orders.total_price)
    ).WHERE((total_spent > 1000) & (nation.region.name == "ASIA"))
    ```

* **Top 5 Most Profitable Nations**
    *Goal: Identify regions with highest revenue.*
    *Code:*
    ```
    selected_regions = nations.WHERE(
        HAS(customers.orders) == 1
    ).CALCULATE(
        region_name=name,
        Total_revenue=SUM(customers.orders.total_price)
    ).TOP_K(5, Total_revenue.DESC())
    ```

* **Inactive Customers**
    *Goal: Find customers who never placed orders.*
    *Code:*
    ```
    customers_without_orders = customers.WHERE(HASNOT(orders)==1).CALCULATE(
        customer_key=key,
        customer_name=name
    )
    ```

* **Customer Activity by Nation**
    *Goal: Track active/inactive customers per nation.*
    *Code:*
    ```
    cust_info = customers.CALCULATE(is_active=HAS(orders)==1)
    nation_summary = nations.CALCULATE(
        nation_name=name,
        total_customers=COUNT(cust_info),
        active_customers=SUM(cust_info.is_active),
        inactive_customers=COUNT(cust_info) - SUM(cust_info.is_active)
    ).ORDER_BY(total_customers.DESC())
    ```

* **High Balance, Low Spending Customers**
    *Goal: Find top 10% in balance but bottom 25% in orders.*
    *Code:*
    ```
    customers_in_low_percentiles = customers.WHERE(
        (PERCENTILE(by=acctbal.DESC()) <= 10) &
        (PERCENTILE(by=COUNT(orders.key).ASC()) <= 25)
    )
    ```

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

* **What is the ticker symbol, month, average closing price, highest price, lowest price**
    ```
    price_info = DailyPrices.CALCULATE(month=JOIN_STRINGS("-", YEAR(date), LPAD(MONTH(date), 2, "0")), symbol=ticker.symbol) # Added comma between arguments and corrected assignment for symbol
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
    TPCH.CALCULATE(avg_n_combo=AVG(size_groups.n_combos)).CALCULATE(
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

---

## **16. GENERAL NOTES**

* **Logical Operators**: Always use `&` (AND), `|` (OR), and `~` (NOT) for logical operations within PyDough expressions. Do **not** use Python's built-in `and`, `or`, `not` keywords, as they have different behaviors and precedence in this context.
* **Chained Inequalities**: For expressions like `a <= b <= c`, avoid chaining them directly. Instead, break them into separate comparisons combined with a logical AND, e.g., `(a <= b) & (b <= c)`, or use the `MONOTONIC` function if appropriate.
* **Aggregation Functions**: Remember that aggregation functions (`SUM`, `COUNT`, `AVG`, `MIN`, `MAX`, etc.) are used to convert plural values (e.g., fields from sub-collections) into singular values that can be used in calculations or returned as a single result.
