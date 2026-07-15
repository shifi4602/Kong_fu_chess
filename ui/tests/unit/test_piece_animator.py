from kungfu_chess.model import PieceState
from ui.animation.piece_animator import PieceAnimator
from ui.assets.sprite_loader import SpriteLoader
from ui.tests.support import FakeCanvas

# Real configs for wP (checked into ui/assets/pieces_mine/wP/states/*/config.json):
#   idle:       4 fps, loop,      -> idle
#   move:       8 fps, loop,      -> long_rest
#   jump:      10 fps, no loop,   -> short_rest   (5 frames => 0.5s)
#   short_rest: 6 fps, no loop,   -> long_rest    (5 frames => 5/6s)
#   long_rest:  2 fps, no loop,   -> idle         (5 frames => 2.5s)


def _animator() -> PieceAnimator:
    loader = SpriteLoader(FakeCanvas(), cell_size=100)
    return PieceAnimator(loader, "wP", now=0.0)


def test_starts_idle_and_loops_forever_while_engine_reports_idle():
    animator = _animator()
    animator.tick(PieceState.IDLE, now=100.0)
    assert animator.visual_state == "idle"


def test_engine_moving_forces_immediate_entry_into_move():
    animator = _animator()
    animator.tick(PieceState.MOVING, now=0.0)
    assert animator.visual_state == "move"

    # "move" loops (8 fps, is_loop=True) -- it never self-exhausts, no
    # matter how long the engine keeps the piece in MOVING.
    animator.tick(PieceState.MOVING, now=50.0)
    assert animator.visual_state == "move"


def test_leaving_moving_chains_through_long_rest_into_idle():
    animator = _animator()
    animator.tick(PieceState.MOVING, now=0.0)
    assert animator.visual_state == "move"

    # Engine settles back to IDLE -- "move" doesn't self-exhaust, so this
    # must be detected explicitly and treated as instant exhaustion.
    animator.tick(PieceState.IDLE, now=1.0)
    assert animator.visual_state == "long_rest"

    # long_rest: 2 fps * 5 frames = 2.5s to exhaust.
    animator.tick(PieceState.IDLE, now=1.0 + 2.4)
    assert animator.visual_state == "long_rest"

    animator.tick(PieceState.IDLE, now=1.0 + 2.6)
    assert animator.visual_state == "idle"


def test_leaving_jumping_chains_through_short_rest_and_long_rest_into_idle():
    animator = _animator()
    animator.tick(PieceState.JUMPING, now=0.0)
    assert animator.visual_state == "jump"

    animator.tick(PieceState.IDLE, now=0.5)
    assert animator.visual_state == "short_rest"

    # short_rest: 6 fps * 5 frames = 5/6s to exhaust.
    animator.tick(PieceState.IDLE, now=0.5 + 0.9)
    assert animator.visual_state == "long_rest"

    animator.tick(PieceState.IDLE, now=0.5 + 0.9 + 2.6)
    assert animator.visual_state == "idle"


def test_current_frame_advances_with_elapsed_time_in_the_idle_loop():
    animator = _animator()
    first = animator.current_frame(now=0.0)
    later = animator.current_frame(now=0.3)  # idle is 4 fps -> frame index 1
    assert first is not later
