from server.persistence import db


def test_memory_connections_are_independent_databases():
    conn1 = db.connect(":memory:")
    conn2 = db.connect(":memory:")

    conn1.execute("INSERT INTO accounts (username, password_hash, password_salt) VALUES (?, ?, ?)", ("alice", b"h", b"s"))
    conn1.commit()

    rows = conn2.execute("SELECT * FROM accounts").fetchall()
    assert rows == []


def test_apply_schema_twice_is_idempotent():
    conn = db.connect(":memory:")
    db.apply_schema(conn)  # must not raise — IF NOT EXISTS


def test_connect_creates_both_tables():
    conn = db.connect(":memory:")
    names = {
        row["name"]
        for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
    }
    assert {"accounts", "games"}.issubset(names)
