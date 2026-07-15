"""Pure diff between two FrameSnapshots -> a list of discrete events.
No engine coupling beyond the plain data already captured in FrameSnapshot.
"""
from __future__ import annotations

from typing import List

from .events import Event, GameOver, PieceCaptured, PieceMoved, PiecePromoted
from .frame_snapshot import FrameSnapshot


def diff_snapshots(previous: FrameSnapshot, current: FrameSnapshot) -> List[Event]:
    events: List[Event] = []

    # Moves/promotions first, captures last -- so a log built from this
    # order reads as "the move happened, then here's what it caused"
    # rather than the other way around.
    for piece_id, curr_record in current.pieces.items():
        prev_record = previous.pieces.get(piece_id)
        if prev_record is None:
            continue

        # A piece's cell only changes at the exact tick its motion settles
        # (see RealTimeArbiter._settle), so this is a reliable "it just
        # completed a move" signal -- not a rule, just a field comparison.
        if prev_record.cell != curr_record.cell:
            events.append(
                PieceMoved(
                    piece_id, curr_record.color, curr_record.kind, prev_record.cell, curr_record.cell
                )
            )

        if prev_record.kind != curr_record.kind:
            events.append(
                PiecePromoted(piece_id, prev_record.kind, curr_record.kind, curr_record.cell)
            )

    for piece_id, prev_record in previous.pieces.items():
        if piece_id not in current.pieces:
            events.append(
                PieceCaptured(piece_id, prev_record.color, prev_record.kind, prev_record.cell)
            )

    if previous.winner is None and current.winner is not None:
        events.append(GameOver(current.winner))

    return events
