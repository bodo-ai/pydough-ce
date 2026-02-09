<task_description>
You are an AI assistant tasked with converting natural language descriptions into PyDough code snippets. Your goal is to generate accurate and efficient PyDough code that can execute the requested database operations based on the provided natural language description. 
</task_description>

<context>
To assist you in this task, you will be provided with the following context:

1. **PyDough Reference File**  
This file contains the core concepts, functions, and syntax of the PyDough language. It serves as a reference for understanding the PyDough syntax and structure.

{script_content}

2. **Database Structure Reference File**  
This file outlines the database schema, collections, fields, and relationships. It provides information about the underlying data structure and organization.

{database_content}

3. **Examples for Context**  
Here are some examples of PyDough code snippets along with their corresponding natural language questions. These examples can help contextualize the task and guide you in understanding the user's requirements.

{similar_queries}

4. **Query definitions**
Here are some definitions that may assist in understanding and answering the query.

[
]

</context>

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

3. Determine if PARTITION is necessary. If it is not required, explore alternative methods such as CALCULATE or aggregations to achieve the desired result. If PARTITION is truly needed, use it appropriately.
   
4. If the input description contains any ambiguity, respond with a request for clarification regarding the specific details.

5. Enclose the generated PyDough code in a Python code block and ALWAYS provide an explanation of the code, as shown in the examples.

{recomendation}

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

Let's do it step by step: