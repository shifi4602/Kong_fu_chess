from kungfu_chess.engine import GameSnapshot
from kungfu_chess.model import Board, Color, Piece, PieceKind, PieceState, Position
from kungfu_chess.realtime import JumpAction, Motion

from server.session.state_mapper import snapshot_to_state_event


def test_snapshot_to_state_event_maps_pieces_motions_jumps():
    board = Board()
    piece = Piece(id="wP60", color=Color.WHITE, kind=PieceKind.PAWN, cell=Position(6, 0), state=PieceState.IDLE)
    board.place(piece, Position(6, 0))

    moving_piece = Piece(
        id="wP61", color=Color.WHITE, kind=PieceKind.PAWN, cell=Position(4, 1), state=PieceState.MOVING
    )
    board.place(moving_piece, Position(4, 1))
    motion = Motion(
        piece=moving_piece,
        src=Position(6, 1),
        dst=Position(4, 1),
        path=(Position(6, 1), Position(5, 1), Position(4, 1)),
        start_time=1.0,
        duration=2.0,
        sequence=0,
    )

    jumping_piece = Piece(
        id="wN62", color=Color.WHITE, kind=PieceKind.KNIGHT, cell=Position(5, 2), state=PieceState.JUMPING
    )
    board.place(jumping_piece, Position(5, 2))
    jump = JumpAction(piece=jumping_piece, cell=Position(5, 2), start_time=0.5, duration=1.0)

    snapshot = GameSnapshot(board=board, motions=[motion], jumps=[jump], winner=None, current_time=3.5)

    event = snapshot_to_state_event(snapshot, trace_id="fixed-trace")

    assert event.trace_id == "fixed-trace"
    assert event.current_time == 3.5
    assert event.winner is None

    piece_ids = {p.id for p in event.pieces}
    assert piece_ids == {"wP60", "wP61", "wN62"}
    idle_record = next(p for p in event.pieces if p.id == "wP60")
    assert idle_record.color == Color.WHITE
    assert idle_record.kind == PieceKind.PAWN
    assert idle_record.cell == Position(6, 0)
    assert idle_record.state == PieceState.IDLE

    assert len(event.motions) == 1
    motion_record = event.motions[0]
    assert motion_record.piece_id == "wP61"
    assert motion_record.src == Position(6, 1)
    assert motion_record.dst == Position(4, 1)
    assert motion_record.path == (Position(6, 1), Position(5, 1), Position(4, 1))
    assert motion_record.start_time == 1.0
    assert motion_record.duration == 2.0

    assert len(event.jumps) == 1
    jump_record = event.jumps[0]
    assert jump_record.piece_id == "wN62"
    assert jump_record.cell == Position(5, 2)
    assert jump_record.start_time == 0.5
    assert jump_record.duration == 1.0


def test_snapshot_to_state_event_generates_trace_id_when_omitted():
    board = Board()
    snapshot = GameSnapshot(board=board, motions=[], jumps=[], winner=Color.BLACK, current_time=0.0)

    event = snapshot_to_state_event(snapshot)

    assert isinstance(event.trace_id, str) and event.trace_id
    assert event.winner == Color.BLACK
    assert event.pieces == ()
    assert event.motions == ()
    assert event.jumps == ()
