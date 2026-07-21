from __future__ import annotations

import uuid
from collections import deque
from typing import Deque, Dict, Tuple

from kungfu_chess.engine import GameEngine
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
from server.transport.outbound_message import OutboundMessage

QueuedCommand = Tuple[str, object]  # (connection_id, MoveCommand | JumpCommand)


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

    @property
    def engine_ms(self) -> int:
        return self._engine_ms

    @property
    def player_ids(self) -> list[str]:
        return list(self._players)

    def player_for(self, connection_id: str) -> PlayerSession:
        return self._players[connection_id]

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

        snapshot = self._engine.get_snapshot()
        if snapshot.winner is not None and self._finished_at_ms is None:
            self._finished_at_ms = self._engine_ms
            self._broadcast(GameOverEvent(trace_id=_new_trace_id(), winner=snapshot.winner))

        broadcast_interval_ms = 1000.0 / self._config.broadcast_hz
        if self._engine_ms - self._last_broadcast_ms >= broadcast_interval_ms:
            self._last_broadcast_ms = self._engine_ms
            self._broadcast(snapshot_to_state_event(snapshot))

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
        player = self._players[connection_id]
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
        player = self._players[connection_id]
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

    def _unicast(self, connection_id: str, event: object) -> None:
        self._bus.publish(
            OUTBOUND,
            OutboundMessage.unicast(
                event, connection_id, session_id=self.session_id, engine_ms=self._engine_ms
            ),
        )

    def _broadcast(self, event: object) -> None:
        self._bus.publish(
            OUTBOUND,
            OutboundMessage.broadcast(
                event, self._players.keys(), session_id=self.session_id, engine_ms=self._engine_ms
            ),
        )
