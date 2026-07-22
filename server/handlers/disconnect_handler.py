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


class _RoomParticipantRemover(Protocol):
    """Same structural seam as `_WaiterQueue`, for `rooms.RoomRegistry` —
    `server.rooms` is also a sibling of `server.handlers` in the
    `server-layers` contract (docs/ROOMS_PLAN.md §14).
    """

    def remove_participant(self, connection_id: str) -> None: ...


class DisconnectHandler:
    """Subscribes to `Topics.LIFECYCLE`, self-registering like
    `ActivityLogger`/`GameResultRecorder`. Three things a closed socket
    can mean, all handled here: it was a still-queued (never paired)
    matchmaking waiter or a still-pending room participant — drop it so a
    dead connection never gets matched/seated — or it was an active
    player or spectator in a `GameSession` — start that player's
    disconnect countdown (`GameSession.mark_disconnected`), or simply
    drop a departed spectator.
    """

    def __init__(
        self,
        bus: EventBus,
        registry: SessionRegistry,
        lobby: _WaiterQueue,
        rooms: _RoomParticipantRemover,
    ) -> None:
        self._registry = registry
        self._lobby = lobby
        self._rooms = rooms
        bus.subscribe(LIFECYCLE, self.handle)

    def handle(self, message: ConnectionClosed) -> None:
        self._lobby.remove_waiter(message.connection_id)
        self._rooms.remove_participant(message.connection_id)
        session = self._registry.find_session_for_connection(message.connection_id)
        if session is not None:
            session.mark_disconnected(message.connection_id, message.now_ms)
            session.remove_spectator(message.connection_id)
            self._registry.remove_spectator(message.connection_id)
