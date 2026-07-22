from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ConnectionClosed:
    """Published on `Topics.LIFECYCLE` (reserved for exactly this since
    `bus/topics.py` was first written) the instant `transport/ws_server.py`
    sees a socket close. Not a wire record — never touches
    `protocol/codec.py` — just an internal envelope, the same role
    `InboundMessage`/`OutboundMessage` play for their topics. Routing this
    through the bus instead of calling `SessionRegistry` directly from
    `transport/` keeps §3's rule intact: "the transport layer never calls
    game logic directly."
    """

    connection_id: str
    now_ms: int
