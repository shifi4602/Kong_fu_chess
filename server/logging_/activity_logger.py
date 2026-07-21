from __future__ import annotations

import json
import time
from typing import Any, Callable, Optional

from server.bus.event_bus import EventBus
from server.bus.topics import INBOUND, OUTBOUND
from server.handlers.command_dispatcher import InboundMessage
from server.protocol import codec
from server.transport.outbound_message import OutboundMessage

Writer = Callable[[str], None]


class ActivityLogger:
    """Subscribes to both `Topics.INBOUND` and `Topics.OUTBOUND` (not
    outbound-only) and writes one JSON line per record: `timestamp`,
    `trace_id`, `connection_id`, `session_id` (when applicable),
    `direction` (`"in"`/`"out"`), the record's own `type`, and —
    for records that flow through `GameSession.advance()` —
    the `engine_ms` they were applied/published at (§4). Deliberately
    just key-value JSON per line, no custom format, so it drops into
    ELK/Grafana-style log ingestion without a translation step.

    Subscribes itself in `__init__` — matching `server/main.py`'s
    composition-root sketch (`ActivityLogger(bus)`, no one needs to hold
    a reference afterward).
    """

    def __init__(self, bus: EventBus, writer: Writer = print) -> None:
        self._writer = writer
        bus.subscribe(INBOUND, self.handle_inbound)
        bus.subscribe(OUTBOUND, self.handle_outbound)

    def handle_inbound(self, message: InboundMessage) -> None:
        self._write(direction="in", record=message.command, connection_id=message.connection.id)

    def handle_outbound(self, message: OutboundMessage) -> None:
        for connection_id in message.recipient_ids:
            self._write(
                direction="out",
                record=message.event,
                connection_id=connection_id,
                session_id=message.session_id,
                engine_ms=message.engine_ms,
            )

    def _write(
        self,
        direction: str,
        record: Any,
        connection_id: str,
        session_id: Optional[str] = None,
        engine_ms: Optional[int] = None,
    ) -> None:
        line = {
            "timestamp": time.time(),
            "trace_id": getattr(record, "trace_id", None),
            "connection_id": connection_id,
            "session_id": session_id,
            "direction": direction,
            "type": codec.type_name_for(record),
            "engine_ms": engine_ms,
        }
        self._writer(json.dumps(line))
