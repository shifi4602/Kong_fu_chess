"""Per-piece animation state machine: decides which sprite frame to show
each tick, given the engine's `PieceState` and the piece's own asset
configs. Depends only on `SpriteLoader` -- no engine rules, no rendering
backend.

Visual states are entered two ways:
  - Forced: the engine enters MOVING/JUMPING -> visual state snaps to
    "move"/"jump" immediately, animation clock resets.
  - Chained: a state's config.json says what to play once it's done
    (`next_state_when_finished`). "move"/"idle" loop forever by design
    (their duration is however long the engine keeps the piece in that
    state), so they never self-advance -- the only way out is the engine
    leaving MOVING/JUMPING, which is treated as instant exhaustion.
"""
from __future__ import annotations

from kungfu_chess.model import PieceState

from ui.assets.sprite_loader import SpriteLoader
from ui.rendering.canvas import ImageHandle

from .anim_clock import AnimClock

_FORCED_STATE = {
    PieceState.MOVING: "move",
    PieceState.JUMPING: "jump",
}


class PieceAnimator:
    def __init__(self, loader: SpriteLoader, code: str, now: float) -> None:
        self._loader = loader
        self._code = code
        self._visual_state = "idle"
        self._entered_at = now

    @property
    def visual_state(self) -> str:
        return self._visual_state

    def tick(self, engine_state: PieceState, now: float) -> None:
        forced = _FORCED_STATE.get(engine_state)
        if forced is not None and forced != self._visual_state:
            self._enter(forced, now)
            return

        sprites = self._loader.load(self._code, self._visual_state)
        elapsed = now - self._entered_at
        clock = AnimClock(sprites.config.frames_per_sec, sprites.config.is_loop)

        # The engine already left MOVING/JUMPING but our loop-forever
        # visual state hasn't been told -- that's the signal to advance.
        left_forced_state = forced is None and self._visual_state in _FORCED_STATE.values()

        if left_forced_state or clock.is_finished(elapsed, len(sprites.frames)):
            self._enter(sprites.config.next_state_when_finished, now)

    def current_frame(self, now: float) -> ImageHandle:
        sprites = self._loader.load(self._code, self._visual_state)
        clock = AnimClock(sprites.config.frames_per_sec, sprites.config.is_loop)
        index = clock.frame_index(now - self._entered_at, len(sprites.frames))
        return sprites.frames[index]

    def _enter(self, visual_state: str, now: float) -> None:
        self._visual_state = visual_state
        self._entered_at = now
