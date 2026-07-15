"""Manual verification tool, not a pytest test: renders a scripted "two
rooks racing to the same square" scenario to a sequence of PNGs (start,
mid-flight, resolved) through the real engine + SceneBuilder + Canvas,
proving Stage 6's core mechanic without a live window or real time
passing. Uses a scripted clock, not SystemClock, so the checkpoints land
exactly where intended.

Run: python -m ui.tests.manual.render_motion_scenario [output_dir]
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Tuple

import kungfu_chess.config as config
from kungfu_chess.engine import GameEngine
from kungfu_chess.input import BoardMapper
from kungfu_chess.io import BoardParser
from kungfu_chess.model import GameState, Position
from kungfu_chess.realtime import IClock, RealTimeArbiter
from kungfu_chess.rules import MoveRequest, default_rule_engine
from ui.animation import SceneBuilder
from ui.assets import SpriteLoader
from ui.platform import OffscreenImgCanvas
from ui.rendering import BoardRenderer, CoordinateMapper


class ScriptedClock(IClock):
    def __init__(self) -> None:
        self._time = 0.0

    def advance(self, seconds: float) -> None:
        self._time += seconds

    def now(self) -> float:
        return self._time


_BOARD_TEXT = """
wR .  .  bR
.  .  .  .
.  .  .  .
.  .  .  .
"""


def _build() -> Tuple[GameEngine, ScriptedClock]:
    board = BoardParser().parse(_BOARD_TEXT)
    state = GameState(board=board)
    clock = ScriptedClock()
    arbiter = RealTimeArbiter(clock, travel_duration=1.0)
    engine = GameEngine(state, default_rule_engine(), arbiter)
    return engine, clock


def render(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    engine, clock = _build()

    assert engine.request_move(MoveRequest(Position(0, 0), Position(0, 3)))
    assert engine.request_move(MoveRequest(Position(0, 3), Position(0, 0)))

    canvas = OffscreenImgCanvas()
    cell = config.CELL_SIZE
    background = canvas.blank_image(cell * 4, cell * 4, color=(60, 90, 60))
    mapper = CoordinateMapper(BoardMapper(cell_size=cell, rows=4, cols=4), cell)
    loader = SpriteLoader(canvas, cell)
    renderer = BoardRenderer(canvas, background)
    scene = SceneBuilder(canvas, mapper, loader)

    checkpoints = [("1_start", 0.0), ("2_mid_flight", 1.0), ("3_resolved", 3.0)]
    elapsed = 0.0
    for label, target_time in checkpoints:
        clock.advance(target_time - elapsed)
        elapsed = target_time
        engine.tick()
        snapshot = engine.get_snapshot()
        placements = scene.build(snapshot, render_now=clock.now())
        renderer.render(placements)
        canvas.save(output_dir / f"{label}.png")

    print(f"wrote frames to {output_dir}")


if __name__ == "__main__":
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("motion_scenario")
    render(out)
