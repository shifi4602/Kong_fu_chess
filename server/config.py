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
        )
