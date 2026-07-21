from kungfu_chess.model import Color

from server.bus.event_bus import EventBus
from server.config import ServerConfig
from server.matchmaking.lobby import Lobby
from server.matchmaking.strategy import FirstTwoJoinersStrategy, Waiter
from server.session.session_factory import GameSessionFactory
from server.session.session_registry import SessionRegistry
from server.transport.connection import FakeConnection


def _make_lobby():
    config = ServerConfig()
    bus = EventBus()
    registry = SessionRegistry(config)
    factory = GameSessionFactory(bus=bus, config=config)
    lobby = Lobby(strategy=FirstTwoJoinersStrategy(), factory=factory, registry=registry)
    return lobby, registry


def test_first_joiner_gets_no_pairing_yet():
    lobby, registry = _make_lobby()
    result = lobby.join(FakeConnection("c1"), "alice", trace_id="t1", now_ms=0)
    assert result is None
    assert len(registry) == 0


def test_second_joiner_completes_pairing():
    lobby, registry = _make_lobby()
    lobby.join(FakeConnection("c1"), "alice", trace_id="t1", now_ms=0)
    result = lobby.join(FakeConnection("c2"), "bob", trace_id="t2", now_ms=100)

    assert result is not None
    assert result.white.username == "alice"
    assert result.white.color == Color.WHITE
    assert result.white_trace_id == "t1"
    assert result.black.username == "bob"
    assert result.black.color == Color.BLACK
    assert result.black_trace_id == "t2"
    assert len(registry) == 1
    assert registry.get(result.session.session_id) is result.session


def test_third_and_fourth_joiners_pair_into_a_second_session():
    lobby, registry = _make_lobby()
    lobby.join(FakeConnection("c1"), "alice", trace_id="t1", now_ms=0)
    first_pair = lobby.join(FakeConnection("c2"), "bob", trace_id="t2", now_ms=0)

    assert lobby.join(FakeConnection("c3"), "carol", trace_id="t3", now_ms=0) is None
    second_pair = lobby.join(FakeConnection("c4"), "dave", trace_id="t4", now_ms=0)

    assert second_pair is not None
    assert second_pair.session.session_id != first_pair.session.session_id
    assert len(registry) == 2


def test_first_two_joiners_strategy_returns_none_with_fewer_than_two():
    strategy = FirstTwoJoinersStrategy()
    waiter = Waiter(connection=FakeConnection("c1"), username="alice", trace_id="t1")
    assert strategy.try_match([]) is None
    assert strategy.try_match([waiter]) is None


def test_first_two_joiners_strategy_matches_first_two_in_order():
    strategy = FirstTwoJoinersStrategy()
    w1 = Waiter(connection=FakeConnection("c1"), username="alice", trace_id="t1")
    w2 = Waiter(connection=FakeConnection("c2"), username="bob", trace_id="t2")
    w3 = Waiter(connection=FakeConnection("c3"), username="carol", trace_id="t3")
    assert strategy.try_match([w1, w2, w3]) == (w1, w2)
