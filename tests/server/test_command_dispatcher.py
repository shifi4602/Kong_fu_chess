from server.bus.event_bus import EventBus
from server.bus.topics import OUTBOUND
from server.clock import FakeWallClock
from server.handlers.command_dispatcher import CommandDispatcher, InboundMessage
from server.handlers.rate_limiter import RateLimiter
from server.protocol.commands import HeartbeatCommand, JoinCommand, MoveCommand
from server.protocol.errors import ErrorCode
from server.protocol.events import ErrorEvent
from server.transport.connection import FakeConnection


class _RecordingHandler:
    def __init__(self):
        self.calls = []

    def handle(self, connection, cmd):
        self.calls.append((connection, cmd))


def _make_dispatcher(burst=20, max_per_second=10.0):
    bus = EventBus()
    received = []
    bus.subscribe(OUTBOUND, lambda message: received.append(message.event))
    clock = FakeWallClock()
    rate_limiter = RateLimiter(max_per_second=max_per_second, burst=burst, clock=clock)
    move_handler = _RecordingHandler()
    join_handler = _RecordingHandler()
    heartbeat_handler = _RecordingHandler()
    dispatcher = CommandDispatcher(
        handlers={
            MoveCommand: move_handler,
            JoinCommand: join_handler,
            HeartbeatCommand: heartbeat_handler,
        },
        bus=bus,
        rate_limiter=rate_limiter,
    )
    return dispatcher, received, move_handler, join_handler, heartbeat_handler


def test_dispatch_routes_to_the_right_handler():
    dispatcher, received, move_handler, join_handler, _ = _make_dispatcher()
    connection = FakeConnection("c1")
    cmd = MoveCommand(trace_id="t1", src=None, dst=None)

    dispatcher.dispatch(InboundMessage(connection=connection, command=cmd))

    assert move_handler.calls == [(connection, cmd)]
    assert join_handler.calls == []


def test_move_command_past_burst_is_rate_limited_and_never_reaches_handler():
    dispatcher, received, move_handler, _, _ = _make_dispatcher(burst=2)
    connection = FakeConnection("c1")

    for i in range(2):
        dispatcher.dispatch(
            InboundMessage(connection=connection, command=MoveCommand(trace_id=f"t{i}", src=None, dst=None))
        )
    assert len(move_handler.calls) == 2

    dispatcher.dispatch(
        InboundMessage(connection=connection, command=MoveCommand(trace_id="over", src=None, dst=None))
    )
    assert len(move_handler.calls) == 2  # never reached the handler

    rate_limited = [e for e in received if isinstance(e, ErrorEvent)]
    assert len(rate_limited) == 1
    assert rate_limited[0].reason == ErrorCode.RATE_LIMITED
    assert rate_limited[0].connection_id == "c1"
    assert rate_limited[0].trace_id == "over"


def test_heartbeat_is_exempt_from_rate_limiting():
    dispatcher, received, _, _, heartbeat_handler = _make_dispatcher(burst=1)
    connection = FakeConnection("c1")

    for i in range(5):
        dispatcher.dispatch(
            InboundMessage(connection=connection, command=HeartbeatCommand(trace_id=f"t{i}", client_send_ms=i))
        )

    assert len(heartbeat_handler.calls) == 5
    assert [e for e in received if isinstance(e, ErrorEvent)] == []


def test_join_is_exempt_from_rate_limiting():
    dispatcher, received, _, join_handler, _ = _make_dispatcher(burst=1)
    connection = FakeConnection("c1")

    for i in range(3):
        dispatcher.dispatch(
            InboundMessage(
                connection=connection, command=JoinCommand(trace_id=f"t{i}", username="alice", password="pw1")
            )
        )

    assert len(join_handler.calls) == 3
