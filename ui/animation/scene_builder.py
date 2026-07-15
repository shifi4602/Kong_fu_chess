"""Combines each piece's animator (visual state / sprite frame) with the
engine's own live motion data to decide, every frame, exactly what to draw
and where.

Two clocks stay separate here: `render_now` paces sprite-frame selection
(cosmetic, wall-clock). `snapshot.current_time` is what positions in-flight
pieces -- interpolation must match what the arbiter already resolved, so
two pieces racing to the same square resolve visually exactly as the
engine resolved them. This module never predicts travel time or diffs
snapshots; it only reads `motion.progress(snapshot.current_time)`.

The piece set for a frame is the union of `board.all_pieces()` and the
pieces referenced by `snapshot.motions`/`snapshot.jumps`, keyed by
`piece.id` -- defensive against a piece being momentarily absent from the
board mid-flight.
"""
from __future__ import annotations

from typing import Dict, List

from kungfu_chess.engine import GameSnapshot
from kungfu_chess.model import Piece, PieceState

from ui.assets import piece_code, SpriteLoader
from ui.rendering.board_renderer import Placement
from ui.rendering.canvas import Canvas
from ui.rendering.coordinate_mapper import CoordinateMapper

from .interpolator import lerp_point
from .piece_animator import PieceAnimator


class SceneBuilder:
    def __init__(self, canvas: Canvas, mapper: CoordinateMapper, loader: SpriteLoader) -> None:
        self._canvas = canvas
        self._mapper = mapper
        self._loader = loader
        self._animators: Dict[str, PieceAnimator] = {}

    def build(self, snapshot: GameSnapshot, render_now: float) -> List[Placement]:
        pieces_by_id: Dict[str, Piece] = {}
        for piece in snapshot.board.all_pieces():
            pieces_by_id[piece.id] = piece
        for motion in snapshot.motions:
            pieces_by_id[motion.piece.id] = motion.piece
        for jump in snapshot.jumps:
            pieces_by_id[jump.piece.id] = jump.piece

        motions_by_id = {motion.piece.id: motion for motion in snapshot.motions}

        placements: List[Placement] = []
        for piece_id, piece in pieces_by_id.items():
            if piece.state == PieceState.CAPTURED:
                continue

            sprite = self._animate(piece_id, piece, render_now)
            size = self._canvas.image_size(sprite)

            motion = motions_by_id.get(piece_id)
            if motion is not None:
                src_px = self._mapper.cell_top_left(motion.src)
                dst_px = self._mapper.cell_top_left(motion.dst)
                pixel = lerp_point(src_px, dst_px, motion.progress(snapshot.current_time))
                x, y = self._mapper.anchor_at(pixel, size)
            else:
                x, y = self._mapper.sprite_anchor(piece.cell, size)

            placements.append((sprite, x, y))

        return placements

    def _animate(self, piece_id: str, piece: Piece, render_now: float):
        animator = self._animators.get(piece_id)
        if animator is None:
            animator = PieceAnimator(self._loader, piece_code(piece.color, piece.kind), render_now)
            self._animators[piece_id] = animator
        animator.tick(piece.state, render_now)
        return animator.current_frame(render_now)
