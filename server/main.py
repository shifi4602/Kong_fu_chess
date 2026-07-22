"""Composition root — the only module allowed to construct concrete
implementations and wire them together (same rule `ui/main.py` already
follows for the UI side, §11). Nothing here is a module-level singleton;
nothing does import-time side effects.
"""
from __future__ import annotations

import asyncio
from typing import Tuple

from server.bus.event_bus import EventBus
from server.bus.topics import INBOUND, LIFECYCLE, OUTBOUND
from server.clock import SystemWallClock, WallClock
from server.config import ServerConfig
from server.handlers.command_dispatcher import CommandDispatcher, InboundMessage
from server.handlers.disconnect_handler import DisconnectHandler
from server.handlers.heartbeat_handler import HeartbeatHandler
from server.handlers.join_handler import JoinHandler
from server.handlers.jump_handler import JumpHandler
from server.handlers.move_handler import MoveHandler
from server.handlers.rate_limiter import RateLimiter
from server.logging_.activity_logger import ActivityLogger
from server.matchmaking.lobby import Lobby
from server.matchmaking.strategy import EloWindowStrategy
from server.persistence import db
from server.persistence.sqlite_game_repository import SqliteGameRepository
from server.persistence.sqlite_user_repository import SqliteUserRepository
from server.protocol.commands import HeartbeatCommand, JoinCommand, JumpCommand, MoveCommand
from server.results.game_result_recorder import GameResultRecorder
from server.rooms.room_registry import RoomRegistry
from server.scheduler import run_forever
from server.session.session_factory import GameSessionFactory
from server.session.session_registry import SessionRegistry
from server.transport import ws_server
from server.transport.connection import Connection
from server.transport.connection_broadcaster import ConnectionBroadcaster
from server.transport.lifecycle import ConnectionClosed


def build_server(
    config: ServerConfig, wall_clock: WallClock
) -> Tuple[EventBus, SessionRegistry, CommandDispatcher, ConnectionBroadcaster, RoomRegistry]:
    bus = EventBus()

    db_conn = db.connect(config.database_path)
    users = SqliteUserRepository(db_conn)
    games = SqliteGameRepository(db_conn)
    registry = SessionRegistry(config)
    factory = GameSessionFactory(bus=bus, config=config)
    strategy = EloWindowStrategy(
        base_window=config.elo_match_base_window,
        window_growth_per_second=config.elo_match_window_growth_per_second,
        max_wait_ms=config.elo_match_max_wait_ms,
    )
    lobby = Lobby(strategy=strategy, factory=factory, registry=registry)
    rooms = RoomRegistry(factory=factory, registry=registry, config=config)

    rate_limiter = RateLimiter(
        max_per_second=config.max_commands_per_second, burst=config.command_burst, clock=wall_clock
    )
    dispatcher = CommandDispatcher(
        handlers={
            JoinCommand: JoinHandler(lobby, users, bus, wall_clock, registry, rooms),
            MoveCommand: MoveHandler(registry),
            JumpCommand: JumpHandler(registry),
            HeartbeatCommand: HeartbeatHandler(registry, bus, wall_clock),
        },
        bus=bus,
        rate_limiter=rate_limiter,
    )
    bus.subscribe(INBOUND, dispatcher.dispatch)

    broadcaster = ConnectionBroadcaster()
    bus.subscribe(OUTBOUND, broadcaster.handle_outbound)

    ActivityLogger(bus)  # subscribes itself, no one needs to hold a reference
    GameResultRecorder(bus, registry, users, games)  # subscribes itself, likewise
    DisconnectHandler(bus, registry, lobby, rooms)  # subscribes itself, likewise

    return bus, registry, dispatcher, broadcaster, rooms


async def run_server(config: ServerConfig, wall_clock: WallClock | None = None) -> None:
    if wall_clock is None:
        wall_clock = SystemWallClock()
    bus, registry, dispatcher, broadcaster, rooms = build_server(config, wall_clock)

    def on_command(connection: Connection, cmd: object) -> None:
        bus.publish(INBOUND, InboundMessage(connection=connection, command=cmd))

    def on_disconnect(connection_id: str) -> None:
        broadcaster.unregister(connection_id)
        bus.publish(LIFECYCLE, ConnectionClosed(connection_id=connection_id, now_ms=wall_clock.now_ms()))

    async with ws_server.serve(
        config,
        on_connect=broadcaster.register,
        on_disconnect=on_disconnect,
        on_command=on_command,
    ):
        await run_forever(registry, wall_clock, config.tick_hz, room_registry=rooms)


def main() -> None:
    config = ServerConfig.from_env()
    asyncio.run(run_server(config))


if __name__ == "__main__":
    main()
