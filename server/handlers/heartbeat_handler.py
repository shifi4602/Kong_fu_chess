from __future__ import annotations

from server.bus.event_bus import EventBus
from server.bus.topics import OUTBOUND
from server.clock import WallClock
from server.protocol.commands import HeartbeatCommand
from server.protocol.events import HeartbeatEvent
from server.session.session_registry import SessionRegistry
from server.transport.connection import Connection
from server.transport.outbound_message import OutboundMessage


class HeartbeatHandler:
    """Updates `PlayerSession.last_heartbeat_ms` on every `HeartbeatCommand`
    (§8) and replies with a `HeartbeatEvent` carrying `server_time_ms` on
    the same clock basis as `StateEvent.current_time` (`GameSession.engine_ms`
    is exactly that basis in milliseconds — see session/manual_clock.py).
    """

    def __init__(self, registry: SessionRegistry, bus: EventBus, wall_clock: WallClock) -> None:
        self._registry = registry
        self._bus = bus
        self._wall_clock = wall_clock

    def handle(self, connection: Connection, cmd: HeartbeatCommand) -> None:
        session = self._registry.find_session_for_connection(connection.id)
        if session is None:
            return

        player = session.player_for(connection.id)
        player.last_heartbeat_ms = self._wall_clock.now_ms()

        self._bus.publish(
            OUTBOUND,
            OutboundMessage.unicast(
                HeartbeatEvent(
                    trace_id=cmd.trace_id,
                    connection_id=connection.id,
                    client_send_ms=cmd.client_send_ms,
                    server_time_ms=session.engine_ms,
                ),
                connection.id,
            ),
        )
