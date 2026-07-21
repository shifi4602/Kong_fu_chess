from __future__ import annotations

import uuid
from typing import Optional

from kungfu_chess.engine import GameSnapshot

from server.protocol.events import StateEvent
from server.protocol.state_records import JumpRecord, MotionRecord, PieceRecord


def snapshot_to_state_event(snapshot: GameSnapshot, trace_id: Optional[str] = None) -> StateEvent:
    """`GameSnapshot` -> `StateEvent`/`PieceRecord`/`MotionRecord`/`JumpRecord`
    (§5) — a pure function. `trace_id` defaults to a fresh one, since a
    periodic broadcast from `advance()`'s own tick has no originating
    command to inherit from (§5).
    """
    if trace_id is None:
        trace_id = str(uuid.uuid4())

    pieces = tuple(
        PieceRecord(id=piece.id, color=piece.color, kind=piece.kind, cell=piece.cell, state=piece.state)
        for piece in snapshot.board.all_pieces()
    )
    motions = tuple(
        MotionRecord(
            piece_id=motion.piece.id,
            src=motion.src,
            dst=motion.dst,
            path=motion.path,
            start_time=motion.start_time,
            duration=motion.duration,
        )
        for motion in snapshot.motions
    )
    jumps = tuple(
        JumpRecord(
            piece_id=jump.piece.id,
            cell=jump.cell,
            start_time=jump.start_time,
            duration=jump.duration,
        )
        for jump in snapshot.jumps
    )

    return StateEvent(
        trace_id=trace_id,
        pieces=pieces,
        motions=motions,
        jumps=jumps,
        current_time=snapshot.current_time,
        winner=snapshot.winner,
    )
