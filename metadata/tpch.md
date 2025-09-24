# PyDough Graph: TPCH
## Collections overview
- `CUSTOMER`
- `LINEITEM`
- `NATION`
- `ORDERS`
- `PART`
- `PARTSUPP`
- `REGION`
- `SUPPLIER`

## `CUSTOMER`
- Columns:
  - `C_CUSTKEY` (numeric)
  - `C_NAME` (string)
  - `C_ADDRESS` (string)
  - `C_NATIONKEY` (numeric)
  - `C_PHONE` (string)
  - `C_ACCTBAL` (numeric)
  - `C_MKTSEGMENT` (string)
  - `C_COMMENT` (string)
- Relationships:
  - `NATION` (reverse of `NATION.CUSTOMERS`)
  - `ORDER` → `ORDERS` (many) (keys: C_CUSTKEY -> O_CUSTKEY)

## `LINEITEM`
- Columns:
  - `L_ORDERKEY` (numeric)
  - `L_PARTKEY` (numeric)
  - `L_SUPPKEY` (numeric)
  - `L_LINENUMBER` (numeric)
  - `L_QUANTITY` (numeric)
  - `L_EXTENDEDPRICE` (numeric)
  - `L_DISCOUNT` (numeric)
  - `L_TAX` (numeric)
  - `L_RETURNFLAG` (string)
  - `L_LINESTATUS` (string)
  - `L_SHIPDATE` (datetime)
  - `L_COMMITDATE` (datetime)
  - `L_RECEIPTDATE` (datetime)
  - `L_SHIPINSTRUCT` (string)
  - `L_SHIPMODE` (string)
  - `L_COMMENT` (string)
- Relationships:
  - `ORDER` (reverse of `ORDERS.LINEITEMS`)
  - `PARTSUPP` (reverse of `PARTSUPP.LINEITEMS`)

## `NATION`
- Columns:
  - `N_NATIONKEY` (numeric)
  - `N_NAME` (string)
  - `N_REGIONKEY` (numeric)
  - `N_COMMENT` (string)
- Relationships:
  - `CUSTOMERS` → `CUSTOMER` (many) (keys: N_NATIONKEY -> C_NATIONKEY)
  - `REGION` (reverse of `REGION.NATIONS`)
  - `SUPPLIERS` → `SUPPLIER` (many) (keys: N_NATIONKEY -> S_NATIONKEY)

## `ORDERS`
- Columns:
  - `O_ORDERKEY` (numeric)
  - `O_CUSTKEY` (numeric)
  - `O_ORDERSTATUS` (string)
  - `O_TOTALPRICE` (numeric)
  - `O_ORDERDATE` (datetime)
  - `O_ORDERPRIORITY` (string)
  - `O_CLERK` (string)
  - `O_SHIPPRIORITY` (numeric)
  - `O_COMMENT` (string)
- Relationships:
  - `LINEITEMS` → `LINEITEM` (many) (keys: O_ORDERKEY -> L_ORDERKEY)
  - `CUSTOMER` (reverse of `CUSTOMER.ORDER`)

## `PART`
- Columns:
  - `P_PARTKEY` (numeric)
  - `P_NAME` (string)
  - `P_MFGR` (string)
  - `P_BRAND` (string)
  - `P_TYPE` (string)
  - `P_SIZE` (numeric)
  - `P_CONTAINER` (string)
  - `P_RETAILPRICE` (numeric)
  - `P_COMMENT` (string)
- Relationships:
  - `PARTSUPPS` → `PARTSUPP` (many) (keys: P_PARTKEY -> PS_PARTKEY)

## `PARTSUPP`
- Columns:
  - `PS_PARTKEY` (numeric)
  - `PS_SUPPKEY` (numeric)
  - `PS_AVAILQTY` (numeric)
  - `PS_SUPPLYCOST` (numeric)
  - `PS_COMMENT` (string)
- Relationships:
  - `LINEITEMS` → `LINEITEM` (many) (keys: PS_PARTKEY -> L_PARTKEY; PS_SUPPKEY -> L_SUPPKEY)
  - `SUPPLIER` (reverse of `SUPPLIER.PARTSUPPS`)
  - `PART` (reverse of `PART.PARTSUPPS`)

## `REGION`
- Columns:
  - `R_REGIONKEY` (numeric)
  - `R_NAME` (string)
  - `R_COMMENT` (string)
- Relationships:
  - `NATIONS` → `NATION` (many) (keys: R_REGIONKEY -> N_REGIONKEY)

## `SUPPLIER`
- Columns:
  - `S_SUPPKEY` (numeric)
  - `S_NAME` (string)
  - `S_ADDRESS` (string)
  - `S_NATIONKEY` (numeric)
  - `S_PHONE` (string)
  - `S_ACCTBAL` (numeric)
  - `S_COMMENT` (string)
- Relationships:
  - `PARTSUPPS` → `PARTSUPP` (many) (keys: S_SUPPKEY -> PS_SUPPKEY)
  - `NATION` (reverse of `NATION.SUPPLIERS`)
