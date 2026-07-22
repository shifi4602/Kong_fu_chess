from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class ServerConfig:
    host: str = "127.0.0.1"
    port: int = 8765
    tick_hz: float = 50.0
    broadcast_hz: float = 10.0
    max_step_ms: int = 250
    max_players_per_session: int = 2
    heartbeat_interval_ms: int = 2000
    heartbeat_timeout_ms: int = 8000
    session_ttl_after_game_over_ms: int = 30_000
    max_commands_per_second: float = 10.0
    command_burst: int = 20
    max_frame_bytes: int = 65_536
    database_path: str = "kungfu_chess.db"
    disconnect_grace_ms: int = 20_000
    elo_match_base_window: int = 100
    elo_match_window_growth_per_second: float = 40.0
    elo_match_max_wait_ms: int = 60_000
    max_spectators_per_room: int = 50
    room_id_max_length: int = 32

    def __post_init__(self) -> None:
        if not (0 <= self.port <= 65535):
            raise ValueError(f"invalid port: {self.port}")
        if self.tick_hz <= 0:
            raise ValueError(f"tick_hz must be positive: {self.tick_hz}")
        if self.broadcast_hz <= 0:
            raise ValueError(f"broadcast_hz must be positive: {self.broadcast_hz}")
        if self.broadcast_hz > self.tick_hz:
            raise ValueError("broadcast_hz cannot exceed tick_hz")
        if self.max_step_ms <= 0:
            raise ValueError(f"max_step_ms must be positive: {self.max_step_ms}")
        if self.max_players_per_session <= 0:
            raise ValueError("max_players_per_session must be positive")
        if self.heartbeat_interval_ms <= 0:
            raise ValueError("heartbeat_interval_ms must be positive")
        if self.heartbeat_timeout_ms <= self.heartbeat_interval_ms:
            raise ValueError("heartbeat_timeout_ms must exceed heartbeat_interval_ms")
        if self.session_ttl_after_game_over_ms <= 0:
            raise ValueError("session_ttl_after_game_over_ms must be positive")
        if self.max_commands_per_second <= 0:
            raise ValueError("max_commands_per_second must be positive")
        if self.command_burst < 1:
            raise ValueError("command_burst must be at least 1")
        if self.max_frame_bytes <= 0:
            raise ValueError("max_frame_bytes must be positive")
        if not self.database_path:
            raise ValueError("database_path must be non-empty")
        if self.disconnect_grace_ms <= 0:
            raise ValueError("disconnect_grace_ms must be positive")
        if self.elo_match_base_window < 0:
            raise ValueError("elo_match_base_window must be non-negative")
        if self.elo_match_window_growth_per_second < 0:
            raise ValueError("elo_match_window_growth_per_second must be non-negative")
        if self.elo_match_max_wait_ms <= 0:
            raise ValueError("elo_match_max_wait_ms must be positive")
        if self.max_spectators_per_room < 0:
            raise ValueError("max_spectators_per_room must be non-negative")
        if self.room_id_max_length < 1:
            raise ValueError("room_id_max_length must be at least 1")

    @classmethod
    def from_env(cls, env: Mapping[str, str] = os.environ) -> "ServerConfig":
        defaults = cls()
        return cls(
            host=env.get("SERVER_HOST", defaults.host),
            port=int(env.get("SERVER_PORT", defaults.port)),
            tick_hz=float(env.get("SERVER_TICK_HZ", defaults.tick_hz)),
            broadcast_hz=float(env.get("SERVER_BROADCAST_HZ", defaults.broadcast_hz)),
            max_step_ms=int(env.get("SERVER_MAX_STEP_MS", defaults.max_step_ms)),
            max_players_per_session=int(
                env.get("SERVER_MAX_PLAYERS_PER_SESSION", defaults.max_players_per_session)
            ),
            heartbeat_interval_ms=int(
                env.get("SERVER_HEARTBEAT_INTERVAL_MS", defaults.heartbeat_interval_ms)
            ),
            heartbeat_timeout_ms=int(
                env.get("SERVER_HEARTBEAT_TIMEOUT_MS", defaults.heartbeat_timeout_ms)
            ),
            session_ttl_after_game_over_ms=int(
                env.get(
                    "SERVER_SESSION_TTL_AFTER_GAME_OVER_MS",
                    defaults.session_ttl_after_game_over_ms,
                )
            ),
            max_commands_per_second=float(
                env.get("SERVER_MAX_COMMANDS_PER_SECOND", defaults.max_commands_per_second)
            ),
            command_burst=int(env.get("SERVER_COMMAND_BURST", defaults.command_burst)),
            max_frame_bytes=int(env.get("SERVER_MAX_FRAME_BYTES", defaults.max_frame_bytes)),
            database_path=env.get("SERVER_DATABASE_PATH", defaults.database_path),
            disconnect_grace_ms=int(
                env.get("SERVER_DISCONNECT_GRACE_MS", defaults.disconnect_grace_ms)
            ),
            elo_match_base_window=int(
                env.get("SERVER_ELO_MATCH_BASE_WINDOW", defaults.elo_match_base_window)
            ),
            elo_match_window_growth_per_second=float(
                env.get(
                    "SERVER_ELO_MATCH_WINDOW_GROWTH_PER_SECOND",
                    defaults.elo_match_window_growth_per_second,
                )
            ),
            elo_match_max_wait_ms=int(
                env.get("SERVER_ELO_MATCH_MAX_WAIT_MS", defaults.elo_match_max_wait_ms)
            ),
            max_spectators_per_room=int(
                env.get("SERVER_MAX_SPECTATORS_PER_ROOM", defaults.max_spectators_per_room)
            ),
            room_id_max_length=int(
                env.get("SERVER_ROOM_ID_MAX_LENGTH", defaults.room_id_max_length)
            ),
        )
