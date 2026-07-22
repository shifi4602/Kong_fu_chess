from __future__ import annotations

from typing import Protocol

from server.bus.event_bus import EventBus
from server.bus.topics import LIFECYCLE
from server.session.session_registry import SessionRegistry
from server.transport.lifecycle import ConnectionClosed


class _WaiterQueue(Protocol):
    """Structural interface for whatever owns the matchmaking queue —
    `matchmaking.Lobby` satisfies this without `handlers/` importing
    `matchmaking/` directly, same seam `join_handler.py`'s `_JoinLobby`
    uses for the same reason (sibling layers in `.importlinter`'s
    `server-layers` contract).
    """

    def remove_waiter(self, connection_id: str) -> None: ...


class DisconnectHandler:
    """Subscribes to `Topics.LIFECYCLE`, self-registering like
    `ActivityLogger`/`GameResultRecorder`. Two things a closed socket can
    mean, both handled here: it was a still-queued (never paired) waiter —
    drop it from the queue so a dead connection never gets matched — or
    it was an active player in a `GameSession` — start that player's
    disconnect countdown (`GameSession.mark_disconnected`).
    """

    def __init__(self, bus: EventBus, registry: SessionRegistry, lobby: _WaiterQueue) -> None:
        self._registry = registry
        self._lobby = lobby
        bus.subscribe(LIFECYCLE, self.handle)

    def handle(self, message: ConnectionClosed) -> None:
        self._lobby.remove_waiter(message.connection_id)
        session = self._registry.find_session_for_connection(message.connection_id)
        if session is not None:
            session.mark_disconnected(message.connection_id, message.now_ms)
