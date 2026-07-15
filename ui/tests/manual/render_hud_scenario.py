"""Manual verification tool, not a pytest test: replays the racing-rooks
capture scenario through the full pipeline (engine + SceneBuilder + event
bus + HUD panels) and dumps a PNG of the final frame, so the sidebar
(score, move log) can be inspected without a live window.

Run: python -m ui.tests.manual.render_hud_scenario [output.png]
"""
from __future__ import annotations

import sys
from pathlib import Path

import kungfu_chess.config as config
from kungfu_chess.engine import GameEngine
from kungfu_chess.input import BoardMapper
from kungfu_chess.io import BoardParser
from kungfu_chess.model import GameState, Position
from kungfu_chess.realtime import IClock, RealTimeArbiter
from kungfu_chess.rules import MoveRequest, default_rule_engine
from ui.animation import SceneBuilder
from ui.assets import SpriteLoader
from ui.assets.asset_paths import BOARD_IMAGE
from ui.events import EventBus, capture_frame_snapshot, diff_snapshots
from ui.hud import HudRenderer, MoveLogPanel, PlayerLabels, ScorePanel, SIDEBAR_WIDTH
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


def render(output_path: Path) -> None:
    board = BoardParser().parse(_BOARD_TEXT)
    state = GameState(board=board)
    clock = ScriptedClock()
    arbiter = RealTimeArbiter(clock, travel_duration=1.0)
    engine = GameEngine(state, default_rule_engine(), arbiter)

    canvas = OffscreenImgCanvas()
    cell = config.CELL_SIZE
    board_width, board_height = cell * 4, cell * 4

    board_image = canvas.load_image(BOARD_IMAGE, size=(board_width, board_height))
    sidebar_bg = canvas.blank_image(board_width + SIDEBAR_WIDTH, board_height, color=(24, 24, 24))
    background = canvas.compose(sidebar_bg, board_image, 0, 0)

    mapper = CoordinateMapper(BoardMapper(cell_size=cell, rows=4, cols=4), cell)
    loader = SpriteLoader(canvas, cell)
    renderer = BoardRenderer(canvas, background)
    scene = SceneBuilder(canvas, mapper, loader)
    hud = HudRenderer(canvas, board_pixel_width=board_width)

    score_panel = ScorePanel()
    move_log = MoveLogPanel(board_rows=4)
    player_labels = PlayerLabels()
    bus = EventBus()
    bus.subscribe(score_panel.handle)
    bus.subscribe(move_log.handle)
    bus.subscribe(player_labels.handle)

    previous_frame = capture_frame_snapshot(engine.get_snapshot())

    engine.request_move(MoveRequest(Position(0, 0), Position(0, 3)))
    engine.request_move(MoveRequest(Position(0, 3), Position(0, 0)))
    clock.advance(3.0)
    engine.tick()

    snapshot = engine.get_snapshot()
    current_frame = capture_frame_snapshot(snapshot)
    bus.publish(diff_snapshots(previous_frame, current_frame))

    placements = scene.build(snapshot, render_now=clock.now())
    renderer.draw(placements)
    hud.draw(player_labels, score_panel, move_log)
    canvas.present()
    canvas.save(output_path)


if __name__ == "__main__":
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("hud_scenario.png")
    render(out)
    print(f"wrote {out}")
