from server.bus.event_bus import EventBus
from server.bus.topics import OUTBOUND
from server.clock import FakeWallClock
from server.config import ServerConfig
from server.handlers.heartbeat_handler import HeartbeatHandler
from server.protocol.commands import HeartbeatCommand
from server.protocol.events import HeartbeatEvent
from server.session.session_factory import GameSessionFactory
from server.session.session_registry import SessionRegistry
from server.transport.connection import FakeConnection


def _paired_session(registry, bus, config, now_ms=0):
    factory = GameSessionFactory(bus=bus, config=config)
    session, players = factory.create(
        white_connection=FakeConnection("white-conn"),
        white_username="alice",
        black_connection=FakeConnection("black-conn"),
        black_username="bob",
        now_ms=now_ms,
    )
    registry.add(session)
    return session, players


def test_heartbeat_updates_last_heartbeat_ms_and_replies():
    config = ServerConfig()
    bus = EventBus()
    received = []
    bus.subscribe(OUTBOUND, lambda message: received.append(message.event))
    registry = SessionRegistry(config)
    session, players = _paired_session(registry, bus, config, now_ms=0)

    session.advance(500)  # engine_ms now 500 (default max_step_ms=250 clamps it to 250)

    wall_clock = FakeWallClock(initial_ms=12345)
    handler = HeartbeatHandler(registry=registry, bus=bus, wall_clock=wall_clock)
    handler.handle(FakeConnection("white-conn"), HeartbeatCommand(trace_id="t1", client_send_ms=999))

    assert players["white-conn"].last_heartbeat_ms == 12345

    heartbeats = [e for e in received if isinstance(e, HeartbeatEvent)]
    assert len(heartbeats) == 1
    assert heartbeats[0].trace_id == "t1"
    assert heartbeats[0].connection_id == "white-conn"
    assert heartbeats[0].client_send_ms == 999
    assert heartbeats[0].server_time_ms == session.engine_ms


def test_heartbeat_from_unknown_connection_is_dropped():
    config = ServerConfig()
    bus = EventBus()
    received = []
    bus.subscribe(OUTBOUND, lambda message: received.append(message.event))
    registry = SessionRegistry(config)
    _paired_session(registry, bus, config)

    handler = HeartbeatHandler(registry=registry, bus=bus, wall_clock=FakeWallClock())
    handler.handle(FakeConnection("stranger"), HeartbeatCommand(trace_id="t1", client_send_ms=1))

    assert [e for e in received if isinstance(e, HeartbeatEvent)] == []
