from kungfu_chess.model import Color, Position

from server.bus.event_bus import EventBus
from server.config import ServerConfig
from server.session.player_session import ConnectionState
from server.session.session_factory import GameSessionFactory
from server.transport.connection import FakeConnection


def test_create_builds_a_standard_starting_position():
    factory = GameSessionFactory(bus=EventBus(), config=ServerConfig())
    white_conn = FakeConnection("c-white")
    black_conn = FakeConnection("c-black")

    session, players = factory.create(
        white_connection=white_conn,
        white_username="alice",
        black_connection=black_conn,
        black_username="bob",
        now_ms=1000,
    )

    assert players["c-white"].color == Color.WHITE
    assert players["c-black"].color == Color.BLACK
    assert players["c-white"].state == ConnectionState.ACTIVE
    assert players["c-white"].last_heartbeat_ms == 1000

    snapshot = session._engine.get_snapshot()
    white_king = snapshot.board.get(Position(7, 4))
    black_king = snapshot.board.get(Position(0, 4))
    assert white_king is not None and white_king.color == Color.WHITE
    assert black_king is not None and black_king.color == Color.BLACK
    assert len(snapshot.board.all_pieces()) == 32


def test_create_generates_session_id_when_omitted():
    factory = GameSessionFactory(bus=EventBus(), config=ServerConfig())
    session, _ = factory.create(
        white_connection=FakeConnection("c1"),
        white_username="a",
        black_connection=FakeConnection("c2"),
        black_username="b",
        now_ms=0,
    )
    assert isinstance(session.session_id, str) and session.session_id


def test_create_uses_explicit_session_id():
    factory = GameSessionFactory(bus=EventBus(), config=ServerConfig())
    session, _ = factory.create(
        white_connection=FakeConnection("c1"),
        white_username="a",
        black_connection=FakeConnection("c2"),
        black_username="b",
        now_ms=0,
        session_id="fixed-id",
    )
    assert session.session_id == "fixed-id"
