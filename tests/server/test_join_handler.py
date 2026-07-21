from kungfu_chess.model import Color

from server.bus.event_bus import EventBus
from server.bus.topics import OUTBOUND
from server.clock import FakeWallClock
from server.config import ServerConfig
from server.handlers.join_handler import JoinHandler
from server.matchmaking.lobby import Lobby
from server.matchmaking.strategy import FirstTwoJoinersStrategy
from server.persistence.user_repository import InMemoryUserRepository
from server.protocol.commands import JoinCommand
from server.protocol.events import PlayerJoinedEvent, WelcomeEvent
from server.session.session_factory import GameSessionFactory
from server.session.session_registry import SessionRegistry
from server.transport.connection import FakeConnection


def _make_join_handler():
    config = ServerConfig()
    bus = EventBus()
    received = []
    bus.subscribe(OUTBOUND, lambda message: received.append(message.event))
    registry = SessionRegistry(config)
    factory = GameSessionFactory(bus=bus, config=config)
    lobby = Lobby(strategy=FirstTwoJoinersStrategy(), factory=factory, registry=registry)
    users = InMemoryUserRepository()
    clock = FakeWallClock(initial_ms=1000)
    handler = JoinHandler(lobby=lobby, users=users, bus=bus, wall_clock=clock)
    return handler, received, users, registry


def test_first_join_publishes_nothing():
    handler, received, users, registry = _make_join_handler()
    handler.handle(FakeConnection("c1"), JoinCommand(trace_id="t1", username="alice"))

    assert received == []
    assert "alice" in users
    assert len(registry) == 0


def test_second_join_publishes_welcome_to_each_and_one_player_joined_broadcast():
    handler, received, users, registry = _make_join_handler()
    handler.handle(FakeConnection("c1"), JoinCommand(trace_id="t1", username="alice"))
    handler.handle(FakeConnection("c2"), JoinCommand(trace_id="t2", username="bob"))

    welcomes = [e for e in received if isinstance(e, WelcomeEvent)]
    joined = [e for e in received if isinstance(e, PlayerJoinedEvent)]

    assert len(welcomes) == 2
    white_welcome = next(w for w in welcomes if w.color == Color.WHITE)
    black_welcome = next(w for w in welcomes if w.color == Color.BLACK)
    assert white_welcome.connection_id == "c1"
    assert white_welcome.trace_id == "t1"
    assert black_welcome.connection_id == "c2"
    assert black_welcome.trace_id == "t2"

    assert len(joined) == 1
    assert joined[0].color == Color.BLACK
    assert joined[0].trace_id == "t2"

    assert len(registry) == 1
    assert "bob" in users
