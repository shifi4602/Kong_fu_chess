from kungfu_chess.model import Position

from server.bus.event_bus import EventBus
from server.config import ServerConfig
from server.handlers.jump_handler import JumpHandler
from server.handlers.move_handler import MoveHandler
from server.protocol.commands import JumpCommand, MoveCommand
from server.session.session_factory import GameSessionFactory
from server.session.session_registry import SessionRegistry
from server.transport.connection import FakeConnection


def _paired_session(registry):
    config = registry._config
    factory = GameSessionFactory(bus=EventBus(), config=config)
    white_conn = FakeConnection("white-conn")
    black_conn = FakeConnection("black-conn")
    session, players = factory.create(
        white_connection=white_conn,
        white_username="alice",
        black_connection=black_conn,
        black_username="bob",
        now_ms=0,
    )
    registry.add(session)
    return session


def test_move_handler_enqueues_onto_the_right_session():
    registry = SessionRegistry(ServerConfig())
    session = _paired_session(registry)
    handler = MoveHandler(registry)

    cmd = MoveCommand(trace_id="t1", src=Position(6, 0), dst=Position(4, 0))
    handler.handle(FakeConnection("white-conn"), cmd)

    assert list(session._pending) == [("white-conn", cmd)]


def test_move_handler_silently_drops_for_unknown_connection():
    registry = SessionRegistry(ServerConfig())
    _paired_session(registry)
    handler = MoveHandler(registry)

    cmd = MoveCommand(trace_id="t1", src=Position(6, 0), dst=Position(4, 0))
    handler.handle(FakeConnection("stranger"), cmd)  # must not raise


def test_jump_handler_enqueues_onto_the_right_session():
    registry = SessionRegistry(ServerConfig())
    session = _paired_session(registry)
    handler = JumpHandler(registry)

    cmd = JumpCommand(trace_id="t2", position=Position(6, 0))
    handler.handle(FakeConnection("black-conn"), cmd)

    assert list(session._pending) == [("black-conn", cmd)]
