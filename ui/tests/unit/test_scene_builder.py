from kungfu_chess.engine import GameEngine
from kungfu_chess.input import BoardMapper
from kungfu_chess.model import Board, Color, GameState, Piece, PieceKind, PieceState, Position
from kungfu_chess.realtime import IClock, RealTimeArbiter
from kungfu_chess.rules import default_rule_engine
from ui.animation.scene_builder import SceneBuilder
from ui.assets import SpriteLoader
from ui.rendering.coordinate_mapper import CoordinateMapper
from ui.tests.support import FakeCanvas


class FakeClock(IClock):
    def __init__(self) -> None:
        self._time = 0.0

    def advance(self, seconds: float) -> None:
        self._time += seconds

    def now(self) -> float:
        return self._time


def _wiring(rows=4, cols=4):
    board = Board(rows, cols)
    state = GameState(board=board)
    clock = FakeClock()
    arbiter = RealTimeArbiter(clock, travel_duration=1.0)
    engine = GameEngine(state, default_rule_engine(), arbiter)
    canvas = FakeCanvas()
    mapper = CoordinateMapper(BoardMapper(cell_size=100, rows=rows, cols=cols), cell_size=100)
    scene = SceneBuilder(canvas, mapper, SpriteLoader(canvas, cell_size=100))
    return engine, state, arbiter, clock, scene, mapper


def _piece(color, kind) -> Piece:
    return Piece(id=f"{color.value}-{kind.value}", color=color, kind=kind, cell=Position(0, 0))


def test_a_stationary_piece_is_placed_at_its_static_cell_anchor():
    engine, state, arbiter, clock, scene, mapper = _wiring()
    piece = _piece(Color.WHITE, PieceKind.ROOK)
    state.board.place(piece, Position(1, 1))

    placements = scene.build(engine.get_snapshot(), render_now=0.0)

    assert len(placements) == 1
    _, x, y = placements[0]
    expected_x, expected_y = mapper.sprite_anchor(Position(1, 1), (100, 100))
    assert (x, y) == (expected_x, expected_y)


def test_a_moving_piece_is_placed_at_the_interpolated_pixel_not_its_stale_board_cell():
    engine, state, arbiter, clock, scene, mapper = _wiring()
    piece = _piece(Color.WHITE, PieceKind.ROOK)
    state.board.place(piece, Position(0, 0))
    arbiter.start_motion(state, Position(0, 0), Position(0, 3))

    clock.advance(1.5)  # halfway through a 3-square, 3.0s motion
    engine.tick()  # current_time only advances via tick()

    placements = scene.build(engine.get_snapshot(), render_now=clock.now())

    assert len(placements) == 1
    _, x, y = placements[0]
    src_px = mapper.cell_top_left(Position(0, 0))
    dst_px = mapper.cell_top_left(Position(0, 3))
    expected_x, expected_y = mapper.anchor_at(
        ((src_px[0] + dst_px[0]) / 2, (src_px[1] + dst_px[1]) / 2), (100, 100)
    )
    assert (x, y) == (expected_x, expected_y)
    # still keyed at src in board._grid, but rendering must not use that
    # stale cell -- it must follow the live interpolation instead.
    assert engine.get_snapshot().board.get(Position(0, 0)) is piece


def test_two_pieces_racing_to_one_square_resolve_visually_as_the_engine_resolved_them():
    engine, state, arbiter, clock, scene, mapper = _wiring()
    white = _piece(Color.WHITE, PieceKind.ROOK)
    black = _piece(Color.BLACK, PieceKind.ROOK)
    state.board.place(white, Position(0, 0))
    state.board.place(black, Position(0, 3))

    arbiter.start_motion(state, Position(0, 0), Position(0, 3))
    arbiter.start_motion(state, Position(0, 3), Position(0, 0))

    # Mid-flight: both pieces should still be drawn, interpolating toward
    # each other -- rendering has no idea yet who will win.
    clock.advance(1.0)
    engine.tick()
    mid_placements = scene.build(engine.get_snapshot(), render_now=clock.now())
    assert len(mid_placements) == 2
    white_start_x, _ = mapper.sprite_anchor(Position(0, 0), (100, 100))
    black_start_x, _ = mapper.sprite_anchor(Position(0, 3), (100, 100))
    drawn_x_positions = {x for _, x, _ in mid_placements}
    # neither piece should still be sitting at its untouched starting cell
    assert white_start_x not in drawn_x_positions
    assert black_start_x not in drawn_x_positions

    # Full resolution: per the engine's own crossing-square rule, white
    # stops one square short (created first) and black is captured.
    clock.advance(2.0)
    engine.tick()
    final_snapshot = engine.get_snapshot()
    assert final_snapshot.board.get(Position(0, 2)) is white
    assert black.state == PieceState.CAPTURED

    final_placements = scene.build(final_snapshot, render_now=clock.now())

    assert len(final_placements) == 1  # the captured piece must not be drawn
    _, x, y = final_placements[0]
    expected_x, expected_y = mapper.sprite_anchor(Position(0, 2), (100, 100))
    assert (x, y) == (expected_x, expected_y)
