from __future__ import annotations

import uuid
from typing import Dict, Tuple

from kungfu_chess import config as engine_config
from kungfu_chess.engine import GameEngine
from kungfu_chess.io import BoardParser
from kungfu_chess.model import Color, GameState
from kungfu_chess.realtime import RealTimeArbiter
from kungfu_chess.rules import default_rule_engine

from server.bus.event_bus import EventBus
from server.config import ServerConfig
from server.session.game_session import GameSession
from server.session.manual_clock import ManualClock
from server.session.player_session import ConnectionState, PlayerSession
from server.transport.connection import Connection

# Server's own copy of the standard starting position, kept independent of
# `ui/main.py`'s `_STANDARD_START` — the server never imports `ui/` (§1).
_STANDARD_START = """
bR bN bB bQ bK bB bN bR
bP bP bP bP bP bP bP bP
.  .  .  .  .  .  .  .
.  .  .  .  .  .  .  .
.  .  .  .  .  .  .  .
.  .  .  .  .  .  .  .
wP wP wP wP wP wP wP wP
wR wN wB wQ wK wB wN wR
"""


class GameSessionFactory:
    """Builds a `GameEngine` exactly like `ui/main.py::build_engine()`
    does (`GameState` -> `RealTimeArbiter(clock)` -> `GameEngine`), wraps
    it in a `GameSession`. The one difference from `ui/main.py`: a
    `ManualClock` instead of `SystemClock`, so the scheduler can drive it
    (§9).
    """

    def __init__(self, bus: EventBus, config: ServerConfig) -> None:
        self._bus = bus
        self._config = config
        self._board_parser = BoardParser()

    def create(
        self,
        white_connection: Connection,
        white_username: str,
        black_connection: Connection,
        black_username: str,
        now_ms: int,
        session_id: str | None = None,
    ) -> Tuple[GameSession, Dict[str, PlayerSession]]:
        if session_id is None:
            session_id = str(uuid.uuid4())

        board = self._board_parser.parse(_STANDARD_START)
        state = GameState(board=board)
        clock = ManualClock(initial_ms=now_ms)
        arbiter = RealTimeArbiter(clock, travel_duration=engine_config.TRAVEL_DURATION)
        engine = GameEngine(state, default_rule_engine(), arbiter)

        white = PlayerSession(
            id=white_connection.id,
            username=white_username,
            connection=white_connection,
            color=Color.WHITE,
            state=ConnectionState.ACTIVE,
            last_heartbeat_ms=now_ms,
        )
        black = PlayerSession(
            id=black_connection.id,
            username=black_username,
            connection=black_connection,
            color=Color.BLACK,
            state=ConnectionState.ACTIVE,
            last_heartbeat_ms=now_ms,
        )
        players = {white.id: white, black.id: black}

        session = GameSession(
            session_id=session_id,
            engine=engine,
            clock=clock,
            players=players,
            config=self._config,
            bus=self._bus,
            now_ms=now_ms,
        )
        return session, players
