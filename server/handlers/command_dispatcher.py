from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Type

from server.bus.event_bus import EventBus
from server.bus.topics import OUTBOUND
from server.handlers.rate_limiter import RateLimiter
from server.protocol.commands import JumpCommand, MoveCommand
from server.protocol.errors import ErrorCode
from server.protocol.events import ErrorEvent
from server.transport.connection import Connection
from server.transport.outbound_message import OutboundMessage


@dataclass(frozen=True)
class InboundMessage:
    """Envelope published on `Topics.INBOUND`: a decoded Command plus
    which connection sent it. The dispatcher (to route to the right
    session) and `ActivityLogger` (to log `connection_id`, §4) both need
    that identity alongside the bare Command.
    """

    connection: Connection
    command: Any


class CommandDispatcher:
    """Command pattern: `{type(cmd): handler}` map, built once in
    `main.py` via DI (§4).
    """

    def __init__(self, handlers: Dict[Type, Any], bus: EventBus, rate_limiter: RateLimiter) -> None:
        self._handlers = handlers
        self._bus = bus
        self._rate_limiter = rate_limiter

    def dispatch(self, message: InboundMessage) -> None:
        connection, cmd = message.connection, message.command
        if isinstance(cmd, (MoveCommand, JumpCommand)) and not self._rate_limiter.allow(connection.id):
            self._bus.publish(
                OUTBOUND,
                OutboundMessage.unicast(
                    ErrorEvent(trace_id=cmd.trace_id, connection_id=connection.id, reason=ErrorCode.RATE_LIMITED),
                    connection.id,
                ),
            )
            return
        self._handlers[type(cmd)].handle(connection, cmd)
