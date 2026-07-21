from __future__ import annotations

from server.protocol.commands import JumpCommand
from server.session.session_registry import SessionRegistry
from server.transport.connection import Connection


class JumpHandler:
    def __init__(self, registry: SessionRegistry) -> None:
        self._registry = registry

    def handle(self, connection: Connection, cmd: JumpCommand) -> None:
        session = self._registry.find_session_for_connection(connection.id)
        if session is None:
            return
        session.enqueue(connection.id, cmd)
