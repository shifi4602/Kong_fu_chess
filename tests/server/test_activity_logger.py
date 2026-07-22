import json

from kungfu_chess.model import Color

from server.bus.event_bus import EventBus
from server.bus.topics import INBOUND, OUTBOUND
from server.handlers.command_dispatcher import InboundMessage
from server.logging_.activity_logger import ActivityLogger
from server.protocol.commands import JoinCommand, MoveCommand
from server.protocol.events import GameOverEvent, WelcomeEvent
from server.transport.connection import FakeConnection
from server.transport.outbound_message import OutboundMessage


def _make_logger():
    bus = EventBus()
    lines = []
    ActivityLogger(bus, writer=lines.append)
    return bus, lines


def test_inbound_command_is_logged_with_direction_in_and_connection_id():
    bus, lines = _make_logger()
    connection = FakeConnection("c1")
    cmd = JoinCommand(trace_id="t1", username="alice", password="pw1")

    bus.publish(INBOUND, InboundMessage(connection=connection, command=cmd))

    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["direction"] == "in"
    assert entry["trace_id"] == "t1"
    assert entry["connection_id"] == "c1"
    assert entry["type"] == "join"
    assert entry["session_id"] is None
    assert entry["engine_ms"] is None
    assert isinstance(entry["timestamp"], float)


def test_outbound_unicast_event_is_logged_once_for_its_one_recipient():
    bus, lines = _make_logger()
    event = WelcomeEvent(trace_id="t2", connection_id="c1", color=Color.WHITE)

    bus.publish(OUTBOUND, OutboundMessage.unicast(event, "c1"))

    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["direction"] == "out"
    assert entry["trace_id"] == "t2"
    assert entry["connection_id"] == "c1"
    assert entry["type"] == "welcome"


def test_outbound_broadcast_event_is_logged_once_per_recipient():
    bus, lines = _make_logger()
    event = GameOverEvent(trace_id="t3", winner=Color.BLACK)

    bus.publish(OUTBOUND, OutboundMessage.broadcast(event, ("c1", "c2"), session_id="s1", engine_ms=5000))

    assert len(lines) == 2
    entries = [json.loads(line) for line in lines]
    connection_ids = {e["connection_id"] for e in entries}
    assert connection_ids == {"c1", "c2"}
    for entry in entries:
        assert entry["trace_id"] == "t3"
        assert entry["type"] == "game_over"
        assert entry["session_id"] == "s1"
        assert entry["engine_ms"] == 5000


def test_inbound_and_outbound_are_correlated_by_trace_id():
    bus, lines = _make_logger()
    connection = FakeConnection("c1")
    move = MoveCommand(trace_id="shared-trace", src=None, dst=None)

    bus.publish(INBOUND, InboundMessage(connection=connection, command=move))
    bus.publish(
        OUTBOUND,
        OutboundMessage.unicast(
            WelcomeEvent(trace_id="shared-trace", connection_id="c1", color=Color.WHITE), "c1"
        ),
    )

    entries = [json.loads(line) for line in lines]
    assert [e["trace_id"] for e in entries] == ["shared-trace", "shared-trace"]
    assert [e["direction"] for e in entries] == ["in", "out"]


def test_logger_subscribes_itself_without_a_held_reference():
    bus = EventBus()
    lines = []
    ActivityLogger(bus, writer=lines.append)  # no reference kept

    bus.publish(
        OUTBOUND, OutboundMessage.unicast(GameOverEvent(trace_id="t4", winner=Color.WHITE), "c1")
    )
    assert len(lines) == 1
