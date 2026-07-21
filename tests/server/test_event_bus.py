from server.bus.event_bus import EventBus
from server.bus.topics import INBOUND, OUTBOUND


def test_publish_calls_only_subscribers_of_that_topic():
    bus = EventBus()
    inbound_received = []
    outbound_received = []
    bus.subscribe(INBOUND, inbound_received.append)
    bus.subscribe(OUTBOUND, outbound_received.append)

    bus.publish(INBOUND, "cmd")
    bus.publish(OUTBOUND, "event")

    assert inbound_received == ["cmd"]
    assert outbound_received == ["event"]


def test_multiple_subscribers_on_same_topic_all_receive():
    bus = EventBus()
    a, b = [], []
    bus.subscribe(INBOUND, a.append)
    bus.subscribe(INBOUND, b.append)

    bus.publish(INBOUND, "x")

    assert a == ["x"]
    assert b == ["x"]


def test_publish_with_no_subscribers_does_not_raise():
    bus = EventBus()
    bus.publish(INBOUND, "no one is listening")
