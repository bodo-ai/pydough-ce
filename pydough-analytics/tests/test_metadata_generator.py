from __future__ import annotations


def test_sqlite_metadata(tmp_path):
    from pydough_analytics.metadata.generator import generate_metadata

    import sqlite3

    db_path = tmp_path / "sample.db"
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(
        "CREATE TABLE customers ("
        "id INTEGER PRIMARY KEY,"
        "name TEXT,"
        "active INTEGER,"
        "created DATE"
        ")"
    )
    cur.execute(
        "CREATE TABLE orders ("
        "id INTEGER PRIMARY KEY,"
        "customer_id INTEGER,"
        "amount REAL,"
        "created_at DATETIME,"
        "FOREIGN KEY(customer_id) REFERENCES customers(id)"
        ")"
    )
    cur.execute(
        "CREATE TABLE invoices ("
        "id INTEGER PRIMARY KEY,"
        "order_id INTEGER,"
        "FOREIGN KEY(order_id) REFERENCES orders(id)"
        ")"
    )
    conn.commit()
    conn.close()

    metadata = generate_metadata(f"sqlite:///{db_path}", graph_name="SHOP")
    assert metadata["name"] == "SHOP"

    collections = {c["name"]: c for c in metadata["collections"]}
    assert set(collections) >= {"customers", "orders", "invoices"}

    customers = {prop["name"]: prop for prop in collections["customers"]["properties"]}
    assert customers["id"]["data type"] == "numeric"
    assert customers["name"]["data type"] == "string"
    assert customers["active"]["data type"] == "numeric"
    assert customers["created"]["data type"] == "datetime"

    relationships = metadata["relationships"]
    forward = [r for r in relationships if r["type"] == "simple join"]
    assert any(
        rel["parent collection"] == "orders" and rel["child collection"] == "invoices"
        for rel in forward
    )

    order_relationship_names = {
        rel["name"]
        for rel in relationships
        if rel.get("parent collection") == "orders"
    }
    assert len(order_relationship_names) == len(
        [rel for rel in relationships if rel.get("parent collection") == "orders"]
    )
