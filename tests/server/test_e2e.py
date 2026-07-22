import asyncio
import contextlib
import time

import pytest
import websockets

from kungfu_chess.model import Color, Position

from server.bus.topics import INBOUND
from server.clock import SystemWallClock
from server.config import ServerConfig
from server.handlers.command_dispatcher import InboundMessage
from server.main import build_server
from server.protocol import codec
from server.protocol.commands import HeartbeatCommand, JoinCommand, MoveCommand
from server.protocol.events import ErrorEvent, HeartbeatEvent, PlayerJoinedEvent, StateEvent, WelcomeEvent
from server.scheduler import run_forever
from server.transport import ws_server


async def _recv_event(ws):
    raw = await asyncio.wait_for(ws.recv(), timeout=5.0)
    return codec.decode_event(raw)


async def _run_join_move_state_heartbeat():
    config = ServerConfig(
        host="127.0.0.1", port=0, tick_hz=100.0, broadcast_hz=50.0, max_step_ms=50, database_path=":memory:"
    )
    wall_clock = SystemWallClock()
    bus, registry, dispatcher, broadcaster, rooms = build_server(config, wall_clock)

    def on_command(connection, cmd):
        bus.publish(INBOUND, InboundMessage(connection=connection, command=cmd))

    async with ws_server.serve(
        config, on_connect=broadcaster.register, on_disconnect=broadcaster.unregister, on_command=on_command
    ) as server:
        port = server.sockets[0].getsockname()[1]
        scheduler_task = asyncio.create_task(run_forever(registry, wall_clock, config.tick_hz))
        try:
            uri = f"ws://127.0.0.1:{port}"
            async with websockets.connect(uri) as client1, websockets.connect(uri) as client2:
                await client1.send(codec.encode(JoinCommand(trace_id="j1", username="alice", password="pw1")))
                await client2.send(codec.encode(JoinCommand(trace_id="j2", username="bob", password="pw2")))

                c1_msgs = [await _recv_event(client1) for _ in range(2)]
                c2_msgs = [await _recv_event(client2) for _ in range(2)]

                c1_welcome = next(e for e in c1_msgs if isinstance(e, WelcomeEvent))
                c2_welcome = next(e for e in c2_msgs if isinstance(e, WelcomeEvent))
                assert {c1_welcome.color, c2_welcome.color} == {Color.WHITE, Color.BLACK}
                assert any(isinstance(e, PlayerJoinedEvent) for e in c1_msgs)
                assert any(isinstance(e, PlayerJoinedEvent) for e in c2_msgs)

                white_client = client1 if c1_welcome.color == Color.WHITE else client2

                await white_client.send(
                    codec.encode(MoveCommand(trace_id="m1", src=Position(6, 0), dst=Position(4, 0)))
                )

                state_event = None
                deadline = time.monotonic() + 5.0
                while time.monotonic() < deadline:
                    event = await _recv_event(white_client)
                    if isinstance(event, StateEvent):
                        moved = any(m.dst == Position(4, 0) for m in event.motions) or any(
                            p.cell == Position(4, 0) for p in event.pieces
                        )
                        if moved:
                            state_event = event
                            break
                assert state_event is not None, "never observed the move reflected in a StateEvent"

                await white_client.send(codec.encode(HeartbeatCommand(trace_id="h1", client_send_ms=42)))
                heartbeat_event = None
                deadline = time.monotonic() + 5.0
                while time.monotonic() < deadline:
                    event = await _recv_event(white_client)
                    if isinstance(event, HeartbeatEvent):
                        heartbeat_event = event
                        break
                assert heartbeat_event is not None
                assert heartbeat_event.client_send_ms == 42

                # Same clock basis as a concurrent StateEvent.current_time (§8).
                assert abs(heartbeat_event.server_time_ms / 1000.0 - state_event.current_time) < 1.0
        finally:
            scheduler_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await scheduler_task


def test_end_to_end_join_move_tick_state_and_heartbeat():
    asyncio.run(_run_join_move_state_heartbeat())


async def _run_oversized_frame_rejected():
    config = ServerConfig(host="127.0.0.1", port=0, max_frame_bytes=64, database_path=":memory:")
    wall_clock = SystemWallClock()
    bus, registry, dispatcher, broadcaster, rooms = build_server(config, wall_clock)

    async with ws_server.serve(
        config,
        on_connect=broadcaster.register,
        on_disconnect=broadcaster.unregister,
        on_command=lambda connection, cmd: None,
    ) as server:
        port = server.sockets[0].getsockname()[1]
        uri = f"ws://127.0.0.1:{port}"
        async with websockets.connect(uri) as client:
            oversized = codec.encode(JoinCommand(trace_id="x" * 500, username="alice", password="pw1"))
            assert len(oversized) > 64
            await client.send(oversized)
            with pytest.raises(websockets.exceptions.ConnectionClosed):
                await asyncio.wait_for(client.recv(), timeout=5.0)


def test_oversized_frame_is_rejected_before_reaching_the_bus():
    asyncio.run(_run_oversized_frame_rejected())


async def _run_unknown_and_malformed_message_get_error_events():
    config = ServerConfig(host="127.0.0.1", port=0, database_path=":memory:")
    wall_clock = SystemWallClock()
    bus, registry, dispatcher, broadcaster, rooms = build_server(config, wall_clock)

    async with ws_server.serve(
        config,
        on_connect=broadcaster.register,
        on_disconnect=broadcaster.unregister,
        on_command=lambda connection, cmd: None,
    ) as server:
        port = server.sockets[0].getsockname()[1]
        uri = f"ws://127.0.0.1:{port}"
        async with websockets.connect(uri) as client:
            await client.send('{"type": "resign", "trace_id": "t1"}')
            event = await _recv_event(client)
            assert event.reason.value == "unknown_command"

            await client.send("not json at all")
            event = await _recv_event(client)
            assert event.reason.value == "malformed_message"


def test_unknown_and_malformed_frames_get_error_events():
    asyncio.run(_run_unknown_and_malformed_message_get_error_events())


async def _run_create_account_disconnect_reconnect():
    config = ServerConfig(host="127.0.0.1", port=0, database_path=":memory:")
    wall_clock = SystemWallClock()
    bus, registry, dispatcher, broadcaster, rooms = build_server(config, wall_clock)

    async with ws_server.serve(
        config,
        on_connect=broadcaster.register,
        on_disconnect=broadcaster.unregister,
        on_command=lambda connection, cmd: bus.publish(
            INBOUND, InboundMessage(connection=connection, command=cmd)
        ),
    ) as server:
        port = server.sockets[0].getsockname()[1]
        uri = f"ws://127.0.0.1:{port}"

        # alice creates her account on first join (no second player yet, so
        # she just waits silently — no WelcomeEvent until paired).
        async with websockets.connect(uri) as alice1:
            await alice1.send(codec.encode(JoinCommand(trace_id="a1", username="alice", password="correct-horse")))
            # Disconnects without ever being paired.

        # alice reconnects with the WRONG password: rejected before pairing.
        async with websockets.connect(uri) as alice_wrong:
            await alice_wrong.send(
                codec.encode(JoinCommand(trace_id="a2", username="alice", password="wrong-password"))
            )
            event = await _recv_event(alice_wrong)
            assert isinstance(event, ErrorEvent)
            assert event.reason.value == "invalid_credentials"

        # alice reconnects with the CORRECT password, and bob joins too:
        # both get paired normally.
        async with websockets.connect(uri) as alice2, websockets.connect(uri) as bob:
            await alice2.send(
                codec.encode(JoinCommand(trace_id="a3", username="alice", password="correct-horse"))
            )
            await bob.send(codec.encode(JoinCommand(trace_id="b1", username="bob", password="pw2")))

            alice_msgs = [await _recv_event(alice2) for _ in range(2)]
            assert any(isinstance(e, WelcomeEvent) for e in alice_msgs)
            assert any(isinstance(e, PlayerJoinedEvent) for e in alice_msgs)


def test_reconnect_with_correct_password_succeeds_and_wrong_password_is_rejected():
    asyncio.run(_run_create_account_disconnect_reconnect())
