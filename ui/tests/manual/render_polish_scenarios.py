"""Manual verification tool, not a pytest test: renders three scripted
scenarios to PNGs proving Stage 9's polish features without a live window:
  - capture_flash.png: the fading overlay right after a capture resolves
  - jump_indicator.png: the overlay on an airborne piece
  - game_over_banner.png: the dimmed board + "<COLOR> WINS" text

Run: python -m ui.tests.manual.render_polish_scenarios [output_dir]
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
from ui.events import PieceCaptured, capture_frame_snapshot, diff_snapshots
from ui.hud import GameOverBanner, PlayerLabels
from ui.platform import OffscreenImgCanvas
from ui.rendering import BoardRenderer, CaptureFlash, CoordinateMapper, JumpIndicator


class ScriptedClock(IClock):
    def __init__(self) -> None:
        self._time = 0.0

    def advance(self, seconds: float) -> None:
        self._time += seconds

    def now(self) -> float:
        return self._time


def _build(board_text: str):
    board = BoardParser().parse(board_text)
    state = GameState(board=board)
    clock = ScriptedClock()
    arbiter = RealTimeArbiter(clock, travel_duration=1.0)
    engine = GameEngine(state, default_rule_engine(), arbiter)
    return engine, clock


def _canvas_and_mapper(rows: int, cols: int):
    canvas = OffscreenImgCanvas()
    cell = config.CELL_SIZE
    background = canvas.blank_image(cell * cols, cell * rows, color=(60, 90, 60))
    mapper = CoordinateMapper(BoardMapper(cell_size=cell, rows=rows, cols=cols), cell)
    return canvas, background, mapper


def render_capture_flash(output_dir: Path) -> None:
    engine, clock = _build("wR .  .  bR\n.  .  .  .\n.  .  .  .\n.  .  .  .")
    canvas, background, mapper = _canvas_and_mapper(4, 4)
    loader = SpriteLoader(canvas, config.CELL_SIZE)
    renderer = BoardRenderer(canvas, background)
    scene = SceneBuilder(canvas, mapper, loader)
    flash = CaptureFlash(canvas, mapper, config.CELL_SIZE)

    previous_frame = capture_frame_snapshot(engine.get_snapshot())
    engine.request_move(MoveRequest(Position(0, 0), Position(0, 3)))
    engine.request_move(MoveRequest(Position(0, 3), Position(0, 0)))
    clock.advance(3.0)
    engine.tick()

    snapshot = engine.get_snapshot()
    events = diff_snapshots(previous_frame, capture_frame_snapshot(snapshot))
    for event in events:
        if isinstance(event, PieceCaptured):
            flash.record(event.cell, clock.now())

    placements = scene.build(snapshot, render_now=clock.now())
    renderer.draw(placements)
    flash.draw(clock.now())
    canvas.present()
    canvas.save(output_dir / "capture_flash.png")


def render_jump_indicator(output_dir: Path) -> None:
    engine, clock = _build("wN .\n.  .")
    canvas, background, mapper = _canvas_and_mapper(2, 2)
    loader = SpriteLoader(canvas, config.CELL_SIZE)
    renderer = BoardRenderer(canvas, background)
    scene = SceneBuilder(canvas, mapper, loader)
    indicator = JumpIndicator(canvas, mapper, config.CELL_SIZE)

    assert engine.request_jump(Position(0, 0))

    snapshot = engine.get_snapshot()
    placements = scene.build(snapshot, render_now=clock.now())
    jumping_cells = [p.cell for p in snapshot.board.all_pieces() if p.state.value == "jumping"]

    renderer.draw(placements)
    indicator.draw(jumping_cells)
    canvas.present()
    canvas.save(output_dir / "jump_indicator.png")


def render_game_over_banner(output_dir: Path) -> None:
    engine, clock = _build("wR .  .  bK\n.  .  .  .\n.  .  .  .\n.  .  .  .")
    canvas, background, mapper = _canvas_and_mapper(4, 4)
    loader = SpriteLoader(canvas, config.CELL_SIZE)
    renderer = BoardRenderer(canvas, background)
    scene = SceneBuilder(canvas, mapper, loader)
    labels = PlayerLabels()
    banner = GameOverBanner(canvas, board_width=config.CELL_SIZE * 4, board_height=config.CELL_SIZE * 4)

    previous_frame = capture_frame_snapshot(engine.get_snapshot())
    engine.request_move(MoveRequest(Position(0, 0), Position(0, 3)))
    clock.advance(3.0)
    engine.tick()

    snapshot = engine.get_snapshot()
    events = diff_snapshots(previous_frame, capture_frame_snapshot(snapshot))
    for event in events:
        labels.handle(event)

    placements = scene.build(snapshot, render_now=clock.now())
    renderer.draw(placements)
    banner.draw(labels)
    canvas.present()
    canvas.save(output_dir / "game_over_banner.png")


if __name__ == "__main__":
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("polish_scenarios")
    out.mkdir(parents=True, exist_ok=True)
    render_capture_flash(out)
    render_jump_indicator(out)
    render_game_over_banner(out)
    print(f"wrote frames to {out}")
