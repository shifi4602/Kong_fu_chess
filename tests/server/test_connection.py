from server.transport.connection import Connection, FakeConnection


def test_fake_connection_records_sent_records_in_order():
    conn = FakeConnection("c1")
    conn.send("first")
    conn.send("second")
    assert conn.sent == ["first", "second"]
    assert conn.id == "c1"


def test_fake_connection_satisfies_connection_protocol():
    conn = FakeConnection("c1")
    assert isinstance(conn, Connection)
