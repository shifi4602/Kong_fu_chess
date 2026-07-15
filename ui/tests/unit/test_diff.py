from kungfu_chess.model import Color, PieceKind, PieceState, Position
from ui.events.diff import diff_snapshots
from ui.events.events import GameOver, PieceCaptured, PieceMoved, PiecePromoted
from ui.events.frame_snapshot import FrameSnapshot, PieceRecord


def _record(color=Color.WHITE, kind=PieceKind.PAWN, state=PieceState.IDLE, cell=Position(0, 0)):
    return PieceRecord(color=color, kind=kind, state=state, cell=cell)


def test_a_piece_missing_from_the_current_frame_is_reported_as_captured():
    previous = FrameSnapshot(
        pieces={"b1": _record(Color.BLACK, PieceKind.KNIGHT, cell=Position(3, 3))},
        winner=None,
    )
    current = FrameSnapshot(pieces={}, winner=None)

    events = diff_snapshots(previous, current)

    assert events == [PieceCaptured("b1", Color.BLACK, PieceKind.KNIGHT, Position(3, 3))]


def test_a_piece_whose_cell_changed_is_reported_as_moved():
    previous = FrameSnapshot(
        pieces={"w1": _record(Color.WHITE, PieceKind.ROOK, cell=Position(3, 0))},
        winner=None,
    )
    current = FrameSnapshot(
        pieces={"w1": _record(Color.WHITE, PieceKind.ROOK, cell=Position(3, 4))},
        winner=None,
    )

    events = diff_snapshots(previous, current)

    assert events == [PieceMoved("w1", Color.WHITE, PieceKind.ROOK, Position(3, 0), Position(3, 4))]


def test_a_pawn_reaching_the_last_row_and_changing_kind_is_reported_as_moved_and_promoted():
    previous = FrameSnapshot(
        pieces={"w1": _record(Color.WHITE, PieceKind.PAWN, cell=Position(1, 0))},
        winner=None,
    )
    current = FrameSnapshot(
        pieces={"w1": _record(Color.WHITE, PieceKind.QUEEN, cell=Position(0, 0))},
        winner=None,
    )

    events = diff_snapshots(previous, current)

    assert events == [
        PieceMoved("w1", Color.WHITE, PieceKind.QUEEN, Position(1, 0), Position(0, 0)),
        PiecePromoted("w1", PieceKind.PAWN, PieceKind.QUEEN, Position(0, 0)),
    ]


def test_a_winner_appearing_is_reported_as_game_over():
    previous = FrameSnapshot(pieces={}, winner=None)
    current = FrameSnapshot(pieces={}, winner=Color.WHITE)

    events = diff_snapshots(previous, current)

    assert events == [GameOver(Color.WHITE)]


def test_no_changes_produce_no_events():
    snapshot = FrameSnapshot(pieces={"w1": _record()}, winner=None)

    assert diff_snapshots(snapshot, snapshot) == []


def test_an_untouched_piece_alongside_a_capture_only_reports_the_capture():
    previous = FrameSnapshot(
        pieces={
            "w1": _record(Color.WHITE, PieceKind.ROOK, cell=Position(0, 0)),
            "b1": _record(Color.BLACK, PieceKind.PAWN, cell=Position(3, 3)),
        },
        winner=None,
    )
    current = FrameSnapshot(
        pieces={"w1": _record(Color.WHITE, PieceKind.ROOK, cell=Position(0, 0))},
        winner=None,
    )

    events = diff_snapshots(previous, current)

    assert events == [PieceCaptured("b1", Color.BLACK, PieceKind.PAWN, Position(3, 3))]
