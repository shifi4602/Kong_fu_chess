from __future__ import annotations

from server.protocol.commands import MoveCommand
from server.session.session_registry import SessionRegistry
from server.transport.connection import Connection


class MoveHandler:
    def __init__(self, registry: SessionRegistry) -> None:
        self._registry = registry

    def handle(self, connection: Connection, cmd: MoveCommand) -> None:
        session = self._registry.find_session_for_connection(connection.id)
        if session is None:
            # No active game for this connection (not yet paired, or its
            # game already ended and was reaped) — nothing to enqueue
            # against. §7's ownership check happens once this is drained.
            return
        session.enqueue(connection.id, cmd)
