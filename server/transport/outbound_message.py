from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional, Tuple


@dataclass(frozen=True)
class OutboundMessage:
    """Internal routing envelope published on the OUTBOUND topic — never
    itself sent over the wire (`protocol/codec.py` only ever encodes
    `event`). §5's wire records deliberately carry no
    `session_id`/recipient-set field (kept minimal for the wire), so
    something has to carry "who should receive this" alongside the event
    for `ConnectionBroadcaster` to route it — that's this envelope.
    Whoever publishes an event (`GameSession`, the join/heartbeat
    handlers, `CommandDispatcher`) is exactly the code that already knows
    its intended recipients, so it's built at the publish call site.

    `session_id`/`engine_ms` are optional and populated only by
    `GameSession` (the one publisher that actually has an engine clock to
    report) — `ActivityLogger` (§4) logs them "when applicable" instead
    of every record needing to fake a value that doesn't apply to it.
    """

    event: Any
    recipient_ids: Tuple[str, ...]
    session_id: Optional[str] = None
    engine_ms: Optional[int] = None

    @classmethod
    def unicast(
        cls,
        event: Any,
        connection_id: str,
        *,
        session_id: Optional[str] = None,
        engine_ms: Optional[int] = None,
    ) -> "OutboundMessage":
        return cls(
            event=event, recipient_ids=(connection_id,), session_id=session_id, engine_ms=engine_ms
        )

    @classmethod
    def broadcast(
        cls,
        event: Any,
        connection_ids,
        *,
        session_id: Optional[str] = None,
        engine_ms: Optional[int] = None,
    ) -> "OutboundMessage":
        return cls(
            event=event,
            recipient_ids=tuple(connection_ids),
            session_id=session_id,
            engine_ms=engine_ms,
        )
