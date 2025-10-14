# Metadata Overview: TPCH (Graph Name)

## Collections
### Collection: `customer` 
- **Description**: No description available.

#### Contains the following scalar properties or columns
- **c_custkey**: No description available.
- **c_name**: No description available.
- **c_address**: No description available.
- **c_nationkey**: No description available.
- **c_phone**: No description available.
- **c_acctbal**: No description available.
- **c_mktsegment**: No description available.
- **c_comment**: No description available.

#### Contains the following sub-collections or relationships
- **nation**: No description available.
  - Related to: `customer.nation`
- **orders**: No description available.
  - Related to: `customer.orders`


### Collection: `lineitem` 
- **Description**: No description available.

#### Contains the following scalar properties or columns
- **l_orderkey**: No description available.
- **l_partkey**: No description available.
- **l_suppkey**: No description available.
- **l_linenumber**: No description available.
- **l_quantity**: No description available.
- **l_extendedprice**: No description available.
- **l_discount**: No description available.
- **l_tax**: No description available.
- **l_returnflag**: No description available.
- **l_linestatus**: No description available.
- **l_shipdate**: No description available.
- **l_commitdate**: No description available.
- **l_receiptdate**: No description available.
- **l_shipinstruct**: No description available.
- **l_shipmode**: No description available.
- **l_comment**: No description available.

#### Contains the following sub-collections or relationships
- **partsupp**: No description available.
  - Related to: `lineitem.partsupp`
- **orders**: No description available.
  - Related to: `lineitem.orders`


### Collection: `nation` 
- **Description**: No description available.

#### Contains the following scalar properties or columns
- **n_nationkey**: No description available.
- **n_name**: No description available.
- **n_regionkey**: No description available.
- **n_comment**: No description available.

#### Contains the following sub-collections or relationships
- **customer**: No description available.
  - Related to: `nation.customer`
- **region**: No description available.
  - Related to: `nation.region`
- **supplier**: No description available.
  - Related to: `nation.supplier`


### Collection: `orders` 
- **Description**: No description available.

#### Contains the following scalar properties or columns
- **o_orderkey**: No description available.
- **o_custkey**: No description available.
- **o_orderstatus**: No description available.
- **o_totalprice**: No description available.
- **o_orderdate**: No description available.
- **o_orderpriority**: No description available.
- **o_clerk**: No description available.
- **o_shippriority**: No description available.
- **o_comment**: No description available.

#### Contains the following sub-collections or relationships
- **lineitem_2**: No description available.
  - Related to: `orders.lineitem`
- **customer**: No description available.
  - Related to: `orders.customer`


### Collection: `part` 
- **Description**: No description available.

#### Contains the following scalar properties or columns
- **p_partkey**: No description available.
- **p_name**: No description available.
- **p_mfgr**: No description available.
- **p_brand**: No description available.
- **p_type**: No description available.
- **p_size**: No description available.
- **p_container**: No description available.
- **p_retailprice**: No description available.
- **p_comment**: No description available.

#### Contains the following sub-collections or relationships
- **partsupp**: No description available.
  - Related to: `part.partsupp`


### Collection: `partsupp` 
- **Description**: No description available.

#### Contains the following scalar properties or columns
- **ps_partkey**: No description available.
- **ps_suppkey**: No description available.
- **ps_availqty**: No description available.
- **ps_supplycost**: No description available.
- **ps_comment**: No description available.

#### Contains the following sub-collections or relationships
- **lineitem**: No description available.
  - Related to: `partsupp.lineitem`
- **part**: No description available.
  - Related to: `partsupp.part`
- **supplier**: No description available.
  - Related to: `partsupp.supplier`


### Collection: `region` 
- **Description**: No description available.

#### Contains the following scalar properties or columns
- **r_regionkey**: No description available.
- **r_name**: No description available.
- **r_comment**: No description available.

#### Contains the following sub-collections or relationships
- **nation**: No description available.
  - Related to: `region.nation`


### Collection: `supplier` 
- **Description**: No description available.

#### Contains the following scalar properties or columns
- **s_suppkey**: No description available.
- **s_name**: No description available.
- **s_address**: No description available.
- **s_nationkey**: No description available.
- **s_phone**: No description available.
- **s_acctbal**: No description available.
- **s_comment**: No description available.

#### Contains the following sub-collections or relationships
- **partsupp_2**: No description available.
  - Related to: `supplier.partsupp`
- **nation_2**: No description available.
  - Related to: `supplier.nation`


