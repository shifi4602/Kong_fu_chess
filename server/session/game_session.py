from __future__ import annotations

import uuid
from collections import deque
from typing import Deque, Dict, FrozenSet, Optional, Set, Tuple

from kungfu_chess.engine import GameEngine
from kungfu_chess.model import Color
from kungfu_chess.rules import MoveRequest

from server.bus.event_bus import EventBus
from server.bus.topics import OUTBOUND
from server.config import ServerConfig
from server.protocol.commands import JumpCommand, MoveCommand
from server.protocol.errors import ErrorCode
from server.protocol.events import GameOverEvent, MoveRejectedEvent
from server.session.manual_clock import ManualClock
from server.session.player_session import ConnectionState, PlayerSession
from server.session.state_mapper import snapshot_to_state_event
from server.transport.connection import Connection
from server.transport.outbound_message import OutboundMessage

QueuedCommand = Tuple[str, object]  # (connection_id, MoveCommand | JumpCommand)


def _other_color(color: Color) -> Color:
    return Color.BLACK if color == Color.WHITE else Color.WHITE


def _new_trace_id() -> str:
    return str(uuid.uuid4())


class GameSession:
    """`GameEngine` + `RealTimeArbiter` (via the engine) + its two
    players. Owns the pending-command deque and `.advance(now_ms)` — pure,
    sync, testable by calling it directly with integers (§9.5).
    """

    def __init__(
        self,
        session_id: str,
        engine: GameEngine,
        clock: ManualClock,
        players: Dict[str, PlayerSession],
        config: ServerConfig,
        bus: EventBus,
        now_ms: int,
    ) -> None:
        self.session_id = session_id
        self._engine = engine
        self._clock = clock
        self._players = players
        self._config = config
        self._bus = bus

        self._pending: Deque[QueuedCommand] = deque()
        self._engine_ms = now_ms
        self._last_now_ms = now_ms
        self._last_broadcast_ms = now_ms
        self._finished_at_ms: int | None = None
        self._spectator_ids: Set[str] = set()

    @property
    def engine_ms(self) -> int:
        return self._engine_ms

    @property
    def player_ids(self) -> list[str]:
        return list(self._players)

    @property
    def spectator_ids(self) -> FrozenSet[str]:
        return frozenset(self._spectator_ids)

    def player_for(self, connection_id: str) -> PlayerSession:
        return self._players[connection_id]

    def add_spectator(self, connection_id: str) -> None:
        self._spectator_ids.add(connection_id)

    def remove_spectator(self, connection_id: str) -> None:
        self._spectator_ids.discard(connection_id)

    def record_heartbeat(self, connection_id: str, now_ms: int) -> None:
        """Updates `PlayerSession.last_heartbeat_ms` for a player; a no-op
        for a spectator (they have no `PlayerSession`, and don't need
        liveness/forfeit tracking — only the `HeartbeatEvent` reply itself,
        which reads `engine_ms`, not this write). Also safe for a stale/
        unknown id, which should never happen given `SessionRegistry`
        only routes here for ids it already indexed.
        """
        player = self._players.get(connection_id)
        if player is not None:
            player.last_heartbeat_ms = now_ms

    @property
    def is_terminal(self) -> bool:
        return self._finished_at_ms is not None

    @property
    def ms_since_finished(self) -> int:
        assert self._finished_at_ms is not None, "ms_since_finished requires is_terminal"
        return self._engine_ms - self._finished_at_ms

    def enqueue(self, connection_id: str, command: object) -> None:
        self._pending.append((connection_id, command))

    def advance(self, now_ms: int) -> None:
        self._drain_pending()

        dt = min(now_ms - self._last_now_ms, self._config.max_step_ms)
        self._last_now_ms = now_ms
        self._engine_ms += dt
        self._clock.set(self._engine_ms)

        self._engine.tick()
        self._check_liveness(now_ms)
        self._check_forfeits(now_ms)

        snapshot = self._engine.get_snapshot()
        if snapshot.winner is not None:
            self._finish(snapshot.winner)

        broadcast_interval_ms = 1000.0 / self._config.broadcast_hz
        if self._engine_ms - self._last_broadcast_ms >= broadcast_interval_ms:
            self._last_broadcast_ms = self._engine_ms
            self._broadcast(snapshot_to_state_event(snapshot))

    def _finish(self, winner: Color) -> None:
        if self._finished_at_ms is not None:
            return
        self._finished_at_ms = self._engine_ms
        self._broadcast(GameOverEvent(trace_id=_new_trace_id(), winner=winner))

    def _drain_pending(self) -> None:
        while self._pending:
            connection_id, command = self._pending.popleft()
            if isinstance(command, MoveCommand):
                self._handle_move(connection_id, command)
            elif isinstance(command, JumpCommand):
                self._handle_jump(connection_id, command)
            else:
                raise TypeError(f"unsupported queued command: {type(command).__name__}")

    def _handle_move(self, connection_id: str, cmd: MoveCommand) -> None:
        player = self._players.get(connection_id)
        if player is None:
            self._unicast(
                connection_id,
                MoveRejectedEvent(
                    trace_id=cmd.trace_id,
                    connection_id=connection_id,
                    reason=ErrorCode.SPECTATOR_CANNOT_ACT,
                ),
            )
            return
        piece = self._engine.get_snapshot().board.get(cmd.src)
        if piece is None or piece.color != player.color:
            self._unicast(
                connection_id,
                MoveRejectedEvent(
                    trace_id=cmd.trace_id, connection_id=connection_id, reason=ErrorCode.NOT_YOUR_PIECE
                ),
            )
            return
        if not self._engine.request_move(MoveRequest(cmd.src, cmd.dst)):
            self._unicast(
                connection_id,
                MoveRejectedEvent(
                    trace_id=cmd.trace_id, connection_id=connection_id, reason=ErrorCode.ILLEGAL_MOVE
                ),
            )

    def _handle_jump(self, connection_id: str, cmd: JumpCommand) -> None:
        player = self._players.get(connection_id)
        if player is None:
            self._unicast(
                connection_id,
                MoveRejectedEvent(
                    trace_id=cmd.trace_id,
                    connection_id=connection_id,
                    reason=ErrorCode.SPECTATOR_CANNOT_ACT,
                ),
            )
            return
        piece = self._engine.get_snapshot().board.get(cmd.position)
        if piece is None or piece.color != player.color:
            self._unicast(
                connection_id,
                MoveRejectedEvent(
                    trace_id=cmd.trace_id, connection_id=connection_id, reason=ErrorCode.NOT_YOUR_PIECE
                ),
            )
            return
        if not self._engine.request_jump(cmd.position):
            self._unicast(
                connection_id,
                MoveRejectedEvent(
                    trace_id=cmd.trace_id, connection_id=connection_id, reason=ErrorCode.ILLEGAL_MOVE
                ),
            )

    def _check_liveness(self, now_ms: int) -> None:
        for player in self._players.values():
            if (
                player.state == ConnectionState.ACTIVE
                and now_ms - player.last_heartbeat_ms > self._config.heartbeat_timeout_ms
            ):
                player.state = ConnectionState.DISCONNECTED
                player.disconnected_at_ms = now_ms

    def _check_forfeits(self, now_ms: int) -> None:
        """The countdown-and-auto-resign policy on top of the
        Active -> Disconnected transition above (docs/SERVER_PLAN.md §6/§16,
        §1's "20-second disconnect countdown"): once a disconnected player
        has been gone for `disconnect_grace_ms`, the other player wins by
        forfeit — "if not, it's like he missed the game." A reconnect
        (`reconnect()` below) clears `disconnected_at_ms` before this ever
        fires, so a player who comes back in time never forfeits.
        """
        if self.is_terminal:
            return
        for player in self._players.values():
            if player.state != ConnectionState.DISCONNECTED or player.disconnected_at_ms is None:
                continue
            if now_ms - player.disconnected_at_ms >= self._config.disconnect_grace_ms:
                player.state = ConnectionState.RESIGNED
                self._finish(_other_color(player.color))
                return

    def mark_disconnected(self, connection_id: str, now_ms: int) -> None:
        """Called from `handlers/disconnect_handler.py` the instant the
        transport layer sees the socket close — faster and more reliable
        than waiting for the heartbeat timeout (§8: "a WebSocket close
        frame is not reliable enough to build [liveness] on alone", but
        when it *does* arrive, acting on it immediately is strictly
        better than waiting out `heartbeat_timeout_ms` first). A no-op if
        `connection_id` no longer names a player in this session (already
        reconnected under a new id) or the player isn't currently ACTIVE
        (already marked disconnected by the heartbeat check, or already
        resigned) — first detection wins, and re-detecting doesn't reset
        the countdown.
        """
        player = self._players.get(connection_id)
        if player is not None and player.state == ConnectionState.ACTIVE:
            player.state = ConnectionState.DISCONNECTED
            player.disconnected_at_ms = now_ms

    def reconnect(self, username: str, connection: Connection, now_ms: int) -> Optional[PlayerSession]:
        """Rebinds `username`'s player to a new `Connection` — "if he
        comes back the game continues like it was" (docs/SERVER_PLAN.md
        §16's "no reconnect identity" gap, closed here by matching on
        username, exactly as that section anticipated). Returns the
        rebound `PlayerSession` (its `.id` is now `connection.id`), or
        `None` if this session has no player with that username, or the
        session already finished (a finished game has nothing to
        reconnect to — the reconnecting client just falls through to
        `Lobby.join()` and starts a new match).
        """
        if self.is_terminal:
            return None
        for old_connection_id, player in list(self._players.items()):
            if player.username != username:
                continue
            del self._players[old_connection_id]
            player.connection = connection
            player.id = connection.id
            player.state = ConnectionState.ACTIVE
            player.disconnected_at_ms = None
            player.last_heartbeat_ms = now_ms
            self._players[connection.id] = player
            return player
        return None

    def _unicast(self, connection_id: str, event: object) -> None:
        self._bus.publish(
            OUTBOUND,
            OutboundMessage.unicast(
                event, connection_id, session_id=self.session_id, engine_ms=self._engine_ms
            ),
        )

    def _broadcast(self, event: object) -> None:
        recipients = list(self._players) + list(self._spectator_ids)
        self._bus.publish(
            OUTBOUND,
            OutboundMessage.broadcast(
                event, recipients, session_id=self.session_id, engine_ms=self._engine_ms
            ),
        )
