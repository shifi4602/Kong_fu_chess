from __future__ import annotations

import asyncio
from typing import Optional

from server.clock import WallClock
from server.rooms.room_registry import RoomRegistry
from server.session.session_registry import SessionRegistry


async def run_forever(
    registry: SessionRegistry,
    wall_clock: WallClock,
    tick_hz: float,
    room_registry: Optional[RoomRegistry] = None,
) -> None:  # pragma: no cover -- exercised by the integration test (§13), not unit tests
    """The ONE async driver loop (§9.1). `now_ms` is read once per
    iteration — the only real read of wall-clock time in the server —
    and shared by every session ticked in that pass. Everything below
    `tick_all` is pure and sync. `room_registry.tick()` (docs/ROOMS_PLAN.md
    §9) piggybacks on the same `now_ms` read to reap rooms whose session
    has already been reaped from `registry`.
    """
    interval = 1.0 / tick_hz
    while True:
        now_ms = wall_clock.now_ms()
        registry.tick_all(now_ms)
        if room_registry is not None:
            room_registry.tick(now_ms)
        await asyncio.sleep(interval)
