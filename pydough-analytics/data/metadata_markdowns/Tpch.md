### The high-level graph `TPCH` collection contains the following columns:
**WARNING**:
TPCH is used ONLY for performing calculations, such as average, sum, count, etc. Do not use it for anything else.
- **customers**: A list of all customer.
- **lines**: A list of all lines items.
- **nations**: A list of all nations.
- **orders**: A list of all orders placed.
- **parts**: A list of all parts available.
- **regions**: A list of all regions.
- **suppliers**: A list of all suppliers
- **supply_records**: A list of all supply records for suppliers and parts.

### The `customers` collection contains the following columns:
- **acctbal**: The account balance of the customer.
- **address**: The address of the customer.
- **comment**: Additional comments or notes about the customer.
- **key**: A unique identifier for the customer.
- **mktsegment**: The market segment the customer belongs to.
- **name**: The name of the customer.
- **nation_key**: A foreign key referencing the `nations` collection.
- **phone**: The customer's phone number.
- **nation**: The corresponding nation of the customer (reverse of `nations.customers`).
- **orders**: A list of all orders placed by the customer (reverse of `orders.customer`).

### The `lines` collection contains the following columns:
- **comment**: Additional comments or notes about the line item.
- **commit_date**: The committed delivery date for the line item.
- **discount**: The discount applied to the line item.
- **extended_price**: The extended price of the line item.
- **line_number**: The line number within the order.
- **order_key**: A foreign key referencing the `orders` collection.
- **part_key**: A foreign key referencing the `parts` collection.
- **quantity**: The quantity ordered.
- **receipt_date**: The date the line item was received.
- **return_flag**: A flag indicating whether the item was returned.
- **ship_date**: The shipping date of the line item.
- **ship_instruct**: Shipping instructions for the line item.
- **ship_mode**: The shipping mode for the line item.
- **status**: The status of the line item.
- **supplier_key**: A foreign key referencing the `suppliers` collection.
- **tax**: The tax applied to the line item.
- **order**: The corresponding order for this line item (reverse of `orders.lines`).
- **part**: The corresponding part for this line item (reverse of `parts.lines`).
- **part_and_supplier**: The corresponding supply record (reverse of `supply_records.lines`).
- **supplier**: The corresponding supplier for this line item (reverse of `suppliers.lines`).

### The `nations` collection contains the following columns:
- **comment**: Additional notes or descriptions about the nation.
- **key**: A unique identifier for the nation.
- **name**: The name of the nation.
- **region_key**: A foreign key referencing the `regions` collection.
- **customers**: A list of customers associated with this nation (reverse of `customers.nation`).
- **region**: The corresponding region this nation belongs to (reverse of `regions.nations`).
- **suppliers**: A list of suppliers associated with this nation (reverse of `suppliers.nation`).

### The `orders` collection contains the following columns:
- **clerk**: The name of the clerk handling the order.
- **comment**: Additional comments or notes about the order.
- **customer_key**: A foreign key referencing the `customers` collection.
- **key**: A unique identifier for the order.
- **order_date**: The date when the order was placed.
- **order_priority**: The priority level of the order (e.g., 'HIGH', 'LOW').
- **order_status**: The current status of the order (e.g., 'PENDING', 'SHIPPED').
- **ship_priority**: The priority level for shipping.
- **total_price**: The total price of the order.
- **customer**: The corresponding customer who placed the order (reverse of `customers.orders`).
- **lines**: A list of all line items in this order (reverse of `lines.order`).

### The `parts` collection contains the following columns:
- **brand**: The brand of the part.
- **comment**: Additional notes or descriptions about the part.
- **container**: The type of container used for packaging the part.
- **key**: A unique identifier for the part.
- **manufacturer**: The manufacturer of the part.
- **name**: The name of the part.
- **part_type**: The type or category of the part.
- **retail_price**: The retail price of the part.
- **size**: The size of the part.
- **lines**: A list of all line items that include this part (reverse of `lines.part`).
- **supply_records**: A list of all supply records for this part (reverse of `supply_records.part`).

### The `regions` collection contains the following columns:
- **comment**: Additional notes or descriptions about the region.
- **key**: A unique identifier for the region.
- **name**: The name of the region.
- **nations**: A list of all nations within this region (reverse of `nations.region`).

### The `suppliers` collection contains the following columns:
- **account_balance**: The account balance of the supplier.
- **address**: The address of the supplier.
- **comment**: Additional notes or descriptions about the supplier.
- **key**: A unique identifier for the supplier.
- **name**: The name of the supplier.
- **nation_key**: A foreign key referencing the `nations` collection.
- **phone**: The supplier's phone number.
- **lines**: A list of all line items supplied by this supplier (reverse of `lines.supplier`).
- **nation**: The corresponding nation of the supplier (reverse of `nations.suppliers`).
- **supply_records**: A list of all supply records for this supplier (reverse of `supply_records.supplier`).

### The `supply_records` collection contains the following columns:
- **availqty**: The available quantity of the part supplied.
- **comment**: Additional notes or descriptions about the supply record.
- **part_key**: A foreign key referencing the `parts` collection.
- **supplier_key**: A foreign key referencing the `suppliers` collection.
- **supplycost**: The cost of supplying this part.
- **lines**: A list of all line items that reference this supply record (reverse of `lines.part_and_supplier`).
- **part**: The corresponding part for this supply record (reverse of `parts.supply_records`).
- **supplier**: The corresponding supplier for this supply record (reverse of `suppliers.supply_records`).

### Getting the total count of orders:
To get the total orders:
```python
total_orders = TPCH.CALCULATE(total_orders= COUNT(orders))
```

### Retrieving Customers for a Nation
To get all customers from a specific nation:
```python
nation_customers = nations.customers.CALCULATE(acctbal, address, comment, key, mktsegment, name, nation_key, phone)
```

### Retrieving the Region for a Nation
For each nation, the corresponding region can be accessed as follows:
```python
nation_region = nations.region.CALCULATE(commnet, key, name)
```

### Retrieving Nations for a Region
To get all nations within a specific region:
```python
region_nations = regions.nations.CALCULATE(comment, key, name, region_key)
```

### Retrieving the Customer for an Order
For each order, the corresponding customer can be accessed as follows:
```python
customer_for_order = orders.customer.CALCULATE(acctbal, address, comment, key, mktsegment, name, nation_key, phone)
```
This allows you to navigate from an order to the customer who placed it.

### Retrieving Orders per Customer
To join all the orders for each customer:
```python
orders_per_customer = customers.orders.CALCULATE(order_key, customer_key, order_status, total_price, order_date, order_priority, clerk, ship_priority, comment)
```

### Retrieving Orders in each nation
To join all the orders you have to join first each customer in each nation like this:
```python
orders_per_customer_in_each_nation = nations.customers.orders.CALCULATE(order_key, customer_key, order_status,total_price, order_date, order_priority, clerk, ship_priority, comment)
```

### Retrieving Suppliers for a Nation
To retrieve all suppliers located in a given nation:
```python
suppliers_in_nation = nations.suppliers.CALCULATE(account_balance, address, comment, key, name, nation_key, phone)
```
### Retrieving Lines for an Order
To retrieve all line items for a given order:
```python
lines_for_order = orders.lines.CALCULATE(comment, commit_date, discount, extended_price, line_number, order_key, part_key, quantity, receipt_date, return_flag, ship_date, ship_instruct, ship_mode, status, supplier_key, tax)
```
### Retrieving the Order for a Line
To retrieve the order associated with a line item, you can query the lines object with the necessary fields:
```python
order_for_line = lines.order.CALCULATE(order_key, customer_key, order_status, total_price, order_date, order_priority, clerk, ship_priority, comment)
```
### Retrieving Parts for a Supplier
To retrieve all parts supplied by a specific supplier:
```python
parts_for_supplier = suppliers.supply_records.part.CALCULATE(brand, comment, container, key, manufacturer, name, part_type, retail_price, size)
```

### Retrieving Suppliers for a Part
To retrieve all suppliers that supply a specific part
```python
suppliers_for_part = parts.supply_records.supplier.CALCULATE(account_balance, address, comment, key, name, nation_key, phone)
```

### Retrieving Suppliers for a Nation
To retrieve all suppliers located in a given nation:
```python
suppliers_in_nation = nations.suppliers.CALCULATE(account_balance, address, comment, key, name, nation_key, phone)
```
