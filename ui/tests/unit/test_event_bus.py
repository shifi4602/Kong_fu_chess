from kungfu_chess.model import Color
from ui.events.event_bus import EventBus
from ui.events.events import GameOver


def test_each_subscriber_receives_every_published_event():
    bus = EventBus()
    received_a = []
    received_b = []
    bus.subscribe(received_a.append)
    bus.subscribe(received_b.append)

    event = GameOver(Color.WHITE)
    bus.publish([event])

    assert received_a == [event]
    assert received_b == [event]


def test_publish_with_no_subscribers_does_not_raise():
    bus = EventBus()
    bus.publish([GameOver(Color.BLACK)])  # should be a no-op, not an error


def test_publish_delivers_multiple_events_in_order():
    bus = EventBus()
    received = []
    bus.subscribe(received.append)

    events = [GameOver(Color.WHITE), GameOver(Color.BLACK)]
    bus.publish(events)

    assert received == events
