from kungfu_chess.model import Color

from server.protocol import codec
from server.protocol.events import GameOverEvent, WelcomeEvent
from server.transport.connection import FakeConnection
from server.transport.connection_broadcaster import ConnectionBroadcaster
from server.transport.outbound_message import OutboundMessage


def test_unicast_sends_only_to_named_connection():
    broadcaster = ConnectionBroadcaster()
    c1 = FakeConnection("c1")
    c2 = FakeConnection("c2")
    broadcaster.register(c1)
    broadcaster.register(c2)

    event = WelcomeEvent(trace_id="t1", connection_id="c1", color=Color.WHITE)
    broadcaster.handle_outbound(OutboundMessage.unicast(event, "c1"))

    assert c1.sent == [codec.encode(event)]
    assert c2.sent == []


def test_broadcast_sends_to_every_named_connection():
    broadcaster = ConnectionBroadcaster()
    c1 = FakeConnection("c1")
    c2 = FakeConnection("c2")
    broadcaster.register(c1)
    broadcaster.register(c2)

    event = GameOverEvent(trace_id="t2", winner=Color.BLACK)
    broadcaster.handle_outbound(OutboundMessage.broadcast(event, ("c1", "c2")))

    encoded = codec.encode(event)
    assert c1.sent == [encoded]
    assert c2.sent == [encoded]


def test_unregistered_connection_is_silently_skipped():
    broadcaster = ConnectionBroadcaster()
    c1 = FakeConnection("c1")
    broadcaster.register(c1)

    event = GameOverEvent(trace_id="t3", winner=Color.WHITE)
    broadcaster.handle_outbound(OutboundMessage.broadcast(event, ("c1", "gone")))  # must not raise

    assert c1.sent == [codec.encode(event)]


def test_unregister_stops_further_delivery():
    broadcaster = ConnectionBroadcaster()
    c1 = FakeConnection("c1")
    broadcaster.register(c1)
    broadcaster.unregister("c1")

    event = GameOverEvent(trace_id="t4", winner=Color.WHITE)
    broadcaster.handle_outbound(OutboundMessage.unicast(event, "c1"))  # must not raise

    assert c1.sent == []
