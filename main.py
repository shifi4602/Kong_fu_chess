import time

import kungfu_chess.config as config
from kungfu_chess.engine import GameEngine
from kungfu_chess.input import BoardMapper, Controller
from kungfu_chess.io import BoardParser, BoardPrinter
from kungfu_chess.model import GameState, Position
from kungfu_chess.realtime import RealTimeArbiter, SystemClock
from kungfu_chess.rules import MoveRequest, default_rule_engine

_INITIAL_BOARD = (
    "bR bN bB bQ bK bB bN bR\n"
    "bP bP bP bP bP bP bP bP\n"
    ". . . . . . . .\n"
    ". . . . . . . .\n"
    ". . . . . . . .\n"
    ". . . . . . . .\n"
    "wP wP wP wP wP wP wP wP\n"
    "wR wN wB wQ wK wB wN wR"
)

_HELP = (
    "Kung Fu Chess - no turns, both sides move simultaneously\n"
    "Pieces travel for {:.1f}s after a move is requested.\n"
    "\n"
    "Commands:\n"
    "  <r1> <c1> <r2> <c2>  request a move  (e.g.  6 0 4 0)\n"
    "  tick                  advance clock and show board\n"
    "  board                 show current board\n"
    "  quit                  exit\n"
)


def _render(printer: BoardPrinter, engine: GameEngine) -> None:
    snap = engine.get_snapshot()
    print()
    print(printer.render(snap.board))
    motions = snap.motions
    if motions:
        print(f"  ({len(motions)} piece(s) in motion)")
    print()


def main() -> None:
    board = BoardParser().parse(_INITIAL_BOARD)
    state = GameState(board=board)
    clock = SystemClock()
    arbiter = RealTimeArbiter(clock, travel_duration=config.TRAVEL_DURATION)
    engine = GameEngine(state, default_rule_engine(), arbiter)
    mapper = BoardMapper(
        cell_size=config.CELL_SIZE,
        rows=config.BOARD_ROWS,
        cols=config.BOARD_COLS,
    )
    controller = Controller(engine, mapper)
    printer = BoardPrinter()

    print(_HELP.format(config.TRAVEL_DURATION))
    _render(printer, engine)

    try:
        while True:
            controller.on_tick()
            snap = engine.get_snapshot()

            if snap.is_over:
                _render(printer, engine)
                print(f"Game over! {snap.winner.name} wins!")
                break

            try:
                raw = input(">>> ").strip()
            except EOFError:
                break

            if not raw or raw == "board":
                _render(printer, engine)
                continue

            if raw == "quit":
                break

            if raw == "tick":
                controller.on_tick()
                _render(printer, engine)
                continue

            parts = raw.split()
            if len(parts) != 4:
                print("Use: row col row col   (e.g.  6 0 4 0)")
                continue

            try:
                r1, c1, r2, c2 = int(parts[0]), int(parts[1]), int(parts[2]), int(parts[3])
            except ValueError:
                print("Coordinates must be integers.")
                continue

            if not engine.request_move(MoveRequest(Position(r1, c1), Position(r2, c2))):
                print("Move not allowed.")
            else:
                print(f"Moving ({r1},{c1}) -> ({r2},{c2})  [arrives in {config.TRAVEL_DURATION}s]")

    except KeyboardInterrupt:
        print("\nGame ended.")


if __name__ == "__main__":
    main()
