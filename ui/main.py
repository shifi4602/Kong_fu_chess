"""Composition root for the Kung-Fu Chess UI.

This module is the only place in ``ui`` allowed to know about every layer at
once (engine, rendering, input). Every other package is wired together here
via constructor injection and never reaches for a global/singleton.
"""
from __future__ import annotations

import time

import kungfu_chess.config as config
from kungfu_chess.engine import GameEngine, GameSnapshot
from kungfu_chess.input import BoardMapper, Controller
from kungfu_chess.io import BoardParser
from kungfu_chess.model import GameState, PieceState
from kungfu_chess.realtime import RealTimeArbiter, SystemClock
from kungfu_chess.rules import default_rule_engine
from ui.animation import FrameClock, SceneBuilder
from ui.assets import SpriteLoader
from ui.assets.asset_paths import BOARD_IMAGE
from ui.events import EventBus, PieceCaptured, capture_frame_snapshot, diff_snapshots
from ui.hud import GameOverBanner, HudRenderer, MoveLogPanel, PlayerLabels, ScorePanel, SIDEBAR_WIDTH
from ui.input import MouseAdapter
from ui.platform import ImgCanvas
from ui.rendering import (
    BoardRenderer,
    Canvas,
    CaptureFlash,
    CoordinateMapper,
    HighlightRenderer,
    JumpIndicator,
)

_STANDARD_START = """
bR bN bB bQ bK bB bN bR
bP bP bP bP bP bP bP bP
.  .  .  .  .  .  .  .
.  .  .  .  .  .  .  .
.  .  .  .  .  .  .  .
.  .  .  .  .  .  .  .
wP wP wP wP wP wP wP wP
wR wN wB wQ wK wB wN wR
"""


def build_engine() -> GameEngine:
    """Parse the standard starting position and wire state + rules + a
    real-time arbiter running on the wall clock. This is the engine-side
    half of the composition root; later stages add a rendering half and a
    frame loop that calls ``engine.tick()`` / ``engine.get_snapshot()``.
    """
    board = BoardParser().parse(_STANDARD_START)
    state = GameState(board=board)
    arbiter = RealTimeArbiter(SystemClock(), travel_duration=config.TRAVEL_DURATION)
    return GameEngine(state, default_rule_engine(), arbiter)


def build_canvas() -> Canvas:
    """The rendering-side half of the composition root. Only this function
    (and no other module outside ``ui/platform``) knows the concrete Canvas
    is an ``ImgCanvas`` -- everything else depends on the ``Canvas``
    protocol from ``ui.rendering``.
    """
    return ImgCanvas(
        window_name="Kung Fu Chess",
        width=config.CELL_SIZE * config.BOARD_COLS + SIDEBAR_WIDTH,
        height=config.CELL_SIZE * config.BOARD_ROWS,
    )


def run_game_loop(engine: GameEngine, canvas: Canvas) -> None:
    """The real-time frame loop: tick the engine, animate every piece,
    render, repeat. Uses its own render clock for animation/FPS pacing --
    deliberately separate from the clock driving the engine's arbiter (the
    "two clocks" rule) -- so cosmetic animation cadence never depends on
    engine tick timing.
    """
    render_clock = SystemClock()
    frame_clock = FrameClock(target_fps=config.FPS)

    board = engine.get_snapshot().board
    board_width = config.CELL_SIZE * config.BOARD_COLS
    board_height = config.CELL_SIZE * config.BOARD_ROWS
    board_mapper = BoardMapper(cell_size=config.CELL_SIZE, rows=board.rows, cols=board.cols)
    mapper = CoordinateMapper(board_mapper, config.CELL_SIZE)
    loader = SpriteLoader(canvas, config.CELL_SIZE)

    board_image = canvas.load_image(BOARD_IMAGE, size=(board_width, board_height))
    sidebar_background = canvas.blank_image(board_width + SIDEBAR_WIDTH, board_height, color=(24, 24, 24))
    background = canvas.compose(sidebar_background, board_image, 0, 0)

    renderer = BoardRenderer(canvas, background)
    highlight = HighlightRenderer(canvas, mapper, config.CELL_SIZE)
    scene = SceneBuilder(canvas, mapper, loader)
    hud = HudRenderer(canvas, board_pixel_width=board_width)
    game_over_banner = GameOverBanner(canvas, board_width, board_height)
    capture_flash = CaptureFlash(canvas, mapper, config.CELL_SIZE)
    jump_indicator = JumpIndicator(canvas, mapper, config.CELL_SIZE)

    controller = Controller(engine, board_mapper)
    mouse_adapter = MouseAdapter(controller)

    score_panel = ScorePanel()
    move_log_panel = MoveLogPanel(board_rows=board.rows)
    player_labels = PlayerLabels()
    event_bus = EventBus()
    event_bus.subscribe(score_panel.handle)
    event_bus.subscribe(move_log_panel.handle)
    event_bus.subscribe(player_labels.handle)
    previous_frame = capture_frame_snapshot(engine.get_snapshot())

    print("Window open. Press Esc or close the window to continue.")
    try:
        while not canvas.should_close():
            now = render_clock.now()
            frame_clock.tick(now)

            mouse_adapter.handle(canvas.poll_events())
            controller.on_tick()
            snapshot = engine.get_snapshot()

            current_frame = capture_frame_snapshot(snapshot)
            frame_events = diff_snapshots(previous_frame, current_frame)
            event_bus.publish(frame_events)
            for event in frame_events:
                if isinstance(event, PieceCaptured):
                    capture_flash.record(event.cell, now)
            previous_frame = current_frame

            placements = scene.build(snapshot, render_now=now)
            jumping_cells = [
                piece.cell for piece in snapshot.board.all_pieces() if piece.state == PieceState.JUMPING
            ]

            renderer.draw(placements)
            highlight.draw(controller.selected)
            jump_indicator.draw(jumping_cells)
            capture_flash.draw(now)
            hud.draw(player_labels, score_panel, move_log_panel)
            game_over_banner.draw(player_labels)

            # The board alternates light/dark squares, so a single flat
            # text color can land on a same-color square and disappear
            # (e.g. white text on the white a8 square). A dark shadow
            # offset by a pixel keeps it legible over either.
            fps_text = f"FPS: {frame_clock.measured_fps:.1f}"
            canvas.draw_text(fps_text, 11, 21, font_size=0.6, color=(0, 0, 0, 255))
            canvas.draw_text(fps_text, 10, 20, font_size=0.6)
            canvas.present()

            remaining = frame_clock.frame_duration - (render_clock.now() - now)
            if remaining > 0:
                time.sleep(remaining)
    finally:
        canvas.close()


def main() -> None:
    engine = build_engine()
    snapshot: GameSnapshot = engine.get_snapshot()
    first_pos, first_piece = next(iter(snapshot.board))
    print(
        f"snapshot ok: {len(snapshot.board.all_pieces())} pieces, "
        f"current_time={snapshot.current_time}, "
        f"first={first_piece.color.value} {first_piece.kind.value} at {first_pos}"
    )

    canvas = build_canvas()
    run_game_loop(engine, canvas)


if __name__ == "__main__":
    main()
