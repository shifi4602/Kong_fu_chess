from __future__ import annotations

from typing import Any, List, Protocol, runtime_checkable


@runtime_checkable
class Connection(Protocol):
    """What `session/` and `handlers/` see instead of a raw socket — the
    only thing that ever crosses the transport/session boundary in that
    direction. `PlayerSession` holds one of these, never a raw
    `websockets` object (§4/§6).
    """

    id: str

    def send(self, record: Any) -> None:
        ...


class FakeConnection:
    """Test double standing in for a real websocket — the same role
    `ui/tests/support/fake_canvas.py` plays for `Canvas`. Records every
    sent record in order so a test can assert on what a connection
    received without touching a real socket.
    """

    def __init__(self, connection_id: str) -> None:
        self.id = connection_id
        self.sent: List[Any] = []

    def send(self, record: Any) -> None:
        self.sent.append(record)
