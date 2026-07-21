from __future__ import annotations

import asyncio
import uuid
from typing import Callable

import websockets

from server.config import ServerConfig
from server.protocol import codec
from server.protocol.errors import ErrorCode
from server.protocol.events import ErrorEvent
from server.transport.connection import Connection

OnConnect = Callable[[Connection], None]
OnDisconnect = Callable[[str], None]
OnCommand = Callable[[Connection, object], None]


class WebSocketConnection:
    """Real `Connection` implementation wrapping a `websockets` server
    connection. `.send()` is sync (per the `Connection` protocol, §4) but
    schedules the actual async write via `asyncio.create_task` — the
    async/sync boundary §9.2 names: a bus subscriber that needs to push
    bytes over a real socket schedules that itself.
    """

    def __init__(self, websocket: "websockets.ServerConnection") -> None:
        self.id = str(uuid.uuid4())
        self._websocket = websocket

    def send(self, raw: str) -> None:
        asyncio.create_task(self._websocket.send(raw))


async def _handle_connection(
    websocket: "websockets.ServerConnection",
    on_connect: OnConnect,
    on_disconnect: OnDisconnect,
    on_command: OnCommand,
) -> None:
    connection = WebSocketConnection(websocket)
    on_connect(connection)
    try:
        async for raw in websocket:
            try:
                cmd = codec.decode_command(raw)
            except codec.UnknownCommandError:
                await websocket.send(
                    codec.encode(
                        ErrorEvent(
                            trace_id=str(uuid.uuid4()),
                            connection_id=connection.id,
                            reason=ErrorCode.UNKNOWN_COMMAND,
                        )
                    )
                )
                continue
            except codec.MalformedMessageError:
                await websocket.send(
                    codec.encode(
                        ErrorEvent(
                            trace_id=str(uuid.uuid4()),
                            connection_id=connection.id,
                            reason=ErrorCode.MALFORMED_MESSAGE,
                        )
                    )
                )
                continue
            on_command(connection, cmd)
    finally:
        on_disconnect(connection.id)


def serve(
    config: ServerConfig,
    on_connect: OnConnect,
    on_disconnect: OnDisconnect,
    on_command: OnCommand,
) -> "websockets.Server":
    """Returns the `websockets.serve(...)` awaitable context manager,
    already bound to this server's callbacks and `max_size` (§9.8). The
    frame-size limit is enforced by the `websockets` library itself,
    before a frame ever reaches `Connection`/the bus — a constructor
    argument, not new code.
    """

    async def handler(websocket: "websockets.ServerConnection") -> None:
        await _handle_connection(websocket, on_connect, on_disconnect, on_command)

    return websockets.serve(handler, config.host, config.port, max_size=config.max_frame_bytes)
