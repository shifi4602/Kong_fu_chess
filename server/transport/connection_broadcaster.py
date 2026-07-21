from __future__ import annotations

from typing import Dict

from server.protocol import codec
from server.transport.connection import Connection
from server.transport.outbound_message import OutboundMessage


class ConnectionBroadcaster:
    """Subscribes to the OUTBOUND topic (wiring done by `server/main.py`,
    the composition root — this class itself never imports `server.bus`,
    since `transport`/`bus` are sibling layers in `.importlinter`'s
    `server-layers` contract). Encodes each event exactly once
    (`protocol/codec.py` is the only file that knows how a record turns
    into bytes) and fans it out to the connections named in the envelope.
    """

    def __init__(self) -> None:
        self._connections: Dict[str, Connection] = {}

    def register(self, connection: Connection) -> None:
        self._connections[connection.id] = connection

    def unregister(self, connection_id: str) -> None:
        self._connections.pop(connection_id, None)

    def handle_outbound(self, message: OutboundMessage) -> None:
        raw = codec.encode(message.event)
        for connection_id in message.recipient_ids:
            connection = self._connections.get(connection_id)
            if connection is not None:
                connection.send(raw)
