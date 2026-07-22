from kungfu_chess.model import Color

from server.bus.event_bus import EventBus
from server.bus.topics import OUTBOUND
from server.config import ServerConfig
from server.persistence.elo import compute_new_ratings
from server.persistence.game_repository import InMemoryGameRepository
from server.persistence.user_repository import InMemoryUserRepository
from server.protocol.events import GameOverEvent, HeartbeatEvent, StateEvent
from server.results.game_result_recorder import GameResultRecorder
from server.session.session_factory import GameSessionFactory
from server.session.session_registry import SessionRegistry
from server.transport.connection import FakeConnection
from server.transport.outbound_message import OutboundMessage


def _make_session(users, config=None, now_ms=0):
    if config is None:
        config = ServerConfig(max_step_ms=10_000)
    bus = EventBus()
    registry = SessionRegistry(config)
    factory = GameSessionFactory(bus=bus, config=config)
    white_conn = FakeConnection("white-conn")
    black_conn = FakeConnection("black-conn")
    session, players = factory.create(
        white_connection=white_conn,
        white_username="alice",
        black_connection=black_conn,
        black_username="bob",
        now_ms=now_ms,
    )
    registry.add(session)
    users.create_account("alice", "pw1")
    users.create_account("bob", "pw2")
    return bus, registry, session


def test_game_over_event_triggers_exactly_one_record_game_call_with_correct_ratings():
    users = InMemoryUserRepository()
    games = InMemoryGameRepository()
    bus, registry, session = _make_session(users)
    GameResultRecorder(bus, registry, users, games)

    bus.publish(
        OUTBOUND,
        OutboundMessage.broadcast(
            GameOverEvent(trace_id="t1", winner=Color.WHITE),
            session.player_ids,
            session_id=session.session_id,
            engine_ms=1000,
        ),
    )

    assert len(games.recorded) == 1
    row = games.recorded[0]
    assert row["session_id"] == session.session_id
    assert row["white_username"] == "alice"
    assert row["black_username"] == "bob"
    assert row["winner_color"] == Color.WHITE

    expected_white_after, expected_black_after = compute_new_ratings(1200, 1200, Color.WHITE)
    assert row["white_rating_before"] == 1200
    assert row["black_rating_before"] == 1200
    assert row["white_rating_after"] == expected_white_after
    assert row["black_rating_after"] == expected_black_after

    assert users.get("alice").elo_rating == expected_white_after
    assert users.get("bob").elo_rating == expected_black_after


def test_outbound_message_with_no_session_id_is_ignored():
    users = InMemoryUserRepository()
    games = InMemoryGameRepository()
    bus, registry, session = _make_session(users)
    GameResultRecorder(bus, registry, users, games)

    bus.publish(
        OUTBOUND,
        OutboundMessage.unicast(
            HeartbeatEvent(trace_id="t2", connection_id="white-conn", client_send_ms=1, server_time_ms=1),
            "white-conn",
        ),
    )

    assert games.recorded == []


def test_state_event_broadcast_is_ignored():
    users = InMemoryUserRepository()
    games = InMemoryGameRepository()
    bus, registry, session = _make_session(users)
    GameResultRecorder(bus, registry, users, games)

    bus.publish(
        OUTBOUND,
        OutboundMessage.broadcast(
            StateEvent(trace_id="t3", pieces=(), motions=(), jumps=(), current_time=1.0, winner=None),
            session.player_ids,
            session_id=session.session_id,
            engine_ms=500,
        ),
    )

    assert games.recorded == []
