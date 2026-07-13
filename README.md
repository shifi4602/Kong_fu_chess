# Kung Fu Chess

Kung Fu Chess is a **real-time** variant of chess: there are no turns. Both
players can move any of their idle pieces at any moment, moves take time to
travel across the board, and a piece can be captured mid-flight. This
repository contains a Python engine for the game — rules, a physics-like
real-time arbiter, board (de)serialization, input handling, and a small
scriptable command runner (`main.py`) that drives the whole pipeline from a
plain-text protocol, which is convenient for testing and automation.

## Table of contents

- [Rules of the game](#rules-of-the-game)
- [Board / command text protocol](#board--command-text-protocol)
- [Architecture](#architecture)
- [Package layout](#package-layout)
- [Design notes](#design-notes)
- [Getting started](#getting-started)
- [Running the tests](#running-the-tests)

## Rules of the game

Kung Fu Chess keeps the standard chess piece set and movement geometry, but
replaces the turn-based clock with a real-time one.

### Pieces and movement

| Piece  | Movement rule |
|--------|---------------|
| King   | One square in any direction (horizontal, vertical, diagonal). |
| Queen  | Any number of empty squares in a straight line or diagonal, path must be clear. |
| Rook   | Any number of empty squares horizontally or vertically, path must be clear. |
| Bishop | Any number of empty squares diagonally, path must be clear. |
| Knight | The standard L-shape (2+1 squares); jumps over other pieces. |
| Pawn   | One square forward if empty; two squares forward from its start row if both squares are empty; one square diagonally forward **only** to capture an enemy piece. |

Movement legality (`kungfu_chess/rules/piece_rules.py`) is geometry-only — it
never considers time or piece state. A separate validation chain
(`kungfu_chess/rules/rule_engine.py`) layers the real-time constraints on
top:

1. **A piece must exist** at the source square.
2. **The piece must be idle** — a piece that is already moving or jumping
   cannot be redirected or start a second action.
3. **The destination must be in bounds and not occupied by a friendly
   piece.**
4. **The piece's own movement geometry must allow the move** (table above).

If all four checks pass, the move is accepted and the piece **starts
traveling** — it does not teleport instantly to its destination the way it
would in classic chess.

### Real time, not turns

This is the core twist. There is no concept of "White to move" / "Black to
move":

- Any piece belonging to either side can be commanded to move at any time,
  as long as that specific piece is idle.
- A move is not instantaneous. Once issued, the piece is in the `MOVING`
  state for a duration proportional to the distance it travels
  (`TRAVEL_DURATION` seconds per square, see [Design notes](#design-notes)).
  While moving, that piece cannot be given a new order.
- Because both sides act concurrently, two pieces can be traveling toward
  the same square from different directions at the same time — the arbiter
  (`RealTimeArbiter`) resolves who actually arrives and what happens on
  collision.
- A `tick`/`wait` step advances the game clock and resolves any actions
  (moves or jumps) whose travel time has elapsed.

### Jumping (Kung Fu defense)

Any idle piece can also perform a **jump in place** instead of moving. A
jump makes the piece briefly airborne (`JUMPING` state) for a fixed
duration. While a piece is jumping:

- It cannot be captured by a normal arriving move from that same square —
  instead, **an enemy piece that arrives at a jumping piece's square is the
  one that gets captured** (the jumper "dodges" and counters). This is the
  defensive maneuver that gives the variant its name.
- If an enemy piece with the same state arrives while the piece is not
  jumping, the normal capture rule applies (see below).
- When the jump duration elapses, the piece lands and returns to `IDLE`.

### Arrival and capture resolution

When a piece's travel time elapses, the arbiter resolves the arrival in this
order:

1. If the piece was captured mid-flight (see jump defense above), the
   arrival is discarded.
2. If the destination square holds an enemy piece that is currently
   **jumping**, the arriving piece is captured instead (the jump defense).
3. If the destination square holds a **friendly** piece by the time of
   arrival, the move fizzles — the arriving piece simply stops and goes
   back to `IDLE` in place (it does not merge or displace its ally).
4. If the destination square holds an **enemy** piece (not jumping), that
   enemy piece is captured and removed, and the arriving piece takes the
   square.
5. Otherwise the square is empty and the piece simply arrives.

Because both sides move concurrently and arrival is resolved only when the
travel timer elapses, two pieces can "pass through" squares that are
momentarily empty when they set off — captures and blocks are only checked
against the state of the board at the *moment of arrival*, not at the
moment the move was requested.

### Pawn promotion

A pawn that arrives on the farthest row from its own starting side (row 0
for White, the last row for Black) is automatically promoted to a **Queen**.

### Winning the game

There is no check, checkmate, or stalemate. The game ends the instant a
**King is captured** — the other side immediately wins. Once a winner is
set, the game is over and no further moves or jumps are accepted.

## Board / command text protocol

`main.py` is a headless driver that reads a simple text protocol from
**stdin** and prints results to **stdout**. This is what the integration
tests (`tests/integration/scripts/*.kfc`, run via `texttests/`) and the
`tests/test_main_pipeline.py` unit tests exercise.

Input has two sections:

```
Board:
<row 0 tokens>
<row 1 tokens>
...
Commands:
<command>
<command>
...
```

**Board tokens** are two characters: a color (`w`/`b`) followed by a piece
letter (`K` `Q` `R` `B` `N` `P`), e.g. `wK`, `bP`. An empty square is a
single `.`. Every row must have the same number of space-separated tokens,
or parsing fails.

**Commands** (one per line, space-separated):

| Command | Effect |
|---------|--------|
| `click X Y` | Simulate a mouse click at pixel `(X, Y)`. First click on an idle piece selects it; a second click on a legal destination issues a move. |
| `jump X Y` | Simulate a jump command at pixel `(X, Y)` — the idle piece there becomes airborne. |
| `wait MS` | Advance the game clock by `MS` milliseconds and resolve any moves/jumps whose timer has elapsed. |
| `print board` | Print the current board state in the same `w`/`b` + letter notation used for input. |

Pixel coordinates are translated to board cells by `BoardMapper`, dividing
by `CELL_SIZE` (see [Design notes](#design-notes)).

**Errors:** if the board section fails to parse, `main.py` prints one of two
error codes and stops before running any commands:

- `ERROR ROW_WIDTH_MISMATCH` — a row does not have the same number of
  tokens as the first row.
- `ERROR UNKNOWN_TOKEN` — a token isn't a valid 2-character piece code (bad
  color letter, bad piece letter, wrong length), or the board section was
  empty.

### Example

```
Board:
wK .
. bK
Commands:
click 0 0
click 100 0
wait 1000
print board
```

The White king at `(0,0)` is selected, then commanded to move one square to
`(0,1)`. `wait 1000` advances the clock by exactly one travel duration
(1 square × 1000 ms/square), which lets the move complete. `print board`
then prints:

```
. wK
. bK
```

## Architecture

The codebase is a layered pipeline. Each layer only knows about the layers
below it:

```
                 ┌───────────────────────┐
   stdin text →  │        main.py        │  → stdout text
                 └───────────┬───────────┘
                              │ orchestrates
        ┌─────────────┬──────┴───────┬───────────────┐
        ▼             ▼              ▼                ▼
   BoardParser   Controller      GameEngine       BoardPrinter
   (io)          (input)         (engine)          (io)
                      │               │
                      ▼               ▼
                BoardMapper      RuleEngine  ───▶ PieceRule (per piece kind)
                (input)          (rules)
                                      │
                                      ▼
                              RealTimeArbiter  ───▶ Motion / JumpAction
                              (realtime)            (realtime)
                                      │
                                      ▼
                                GameState / Board
                                (model)
```

- **`model`** — the data layer. Plain, dependency-free dataclasses/enums:
  `Position`, `Piece`, `Color`, `PieceKind`, `PieceState`, `Board`,
  `GameState`. `Board` is a sparse `{Position: Piece}` map; it knows nothing
  about chess rules.
- **`rules`** — pure move *legality*. `piece_rules.py` has one `PieceRule`
  strategy class per piece kind, each answering "is this geometrically a
  legal move on this board?" with no notion of time. `rule_engine.py`
  chains together a list of `MoveValidator`s (piece exists → piece idle →
  destination legal → geometry legal) into a `RuleEngine.can_move()` used as
  a gate before any move is allowed to *start*.
- **`realtime`** — the clock-driven layer that makes this "kung fu" chess
  instead of classic chess. `Motion` and `JumpAction` are immutable records
  of an in-flight action with a start time and duration. `RealTimeArbiter`
  owns the lists of active motions/jumps, advances them on `tick()`, and
  applies arrival/capture/promotion resolution once a timer elapses. It
  depends on an `IClock` abstraction (`SystemClock` for wall-clock time,
  or a fake clock for deterministic tests) so game logic never calls
  `time.time()` directly.
- **`engine`** — `GameEngine` is the façade that ties `RuleEngine` and
  `RealTimeArbiter` together against a `GameState`: `request_move`,
  `request_jump`, `tick`, and `get_snapshot()` (an immutable
  `GameSnapshot` combining the board, active motions/jumps, winner, and
  clock time — the read model for anything that needs to render or inspect
  the game).
- **`input`** — translates raw UI input into engine calls.
  `BoardMapper` converts pixel coordinates to board `Position`s (and back).
  `Controller` holds click-selection state (which square is currently
  selected) and turns a sequence of clicks into
  `engine.request_move(...)` / `engine.request_jump(...)` calls.
- **`io`** — text (de)serialization only. `BoardParser` turns the
  `w`/`b` + letter board notation into a `Board`; `BoardPrinter` renders a
  `Board` back to that same notation. Neither knows about rules, timing, or
  input.
- **`config`** — a few constants shared across layers (`CELL_SIZE`,
  `TRAVEL_DURATION`, `BOARD_ROWS`, `BOARD_COLS`, `FPS`).
- **`main.py`** — the composition root. It has no game logic of its own: it
  parses the stdin protocol, wires up one instance of each layer
  (parser → state → arbiter → engine → mapper → controller → printer), and
  replays the `Commands:` section against that pipeline, using a
  deterministic `_FakeClock` (advanced only by explicit `wait` commands)
  rather than wall-clock time so that scripted runs are fully reproducible.

### Testing harness

There's a second, independent way to exercise the same engine: a tiny
text-script DSL under `texttests/` (`script_parser.py` parses `.kfc` files
like `tests/integration/scripts/*.kfc`, `script_runner.py` executes them
against the real engine classes directly — `BOARD`, `CLICK row col`,
`TICK seconds`, `ASSERT_CELL`, `ASSERT_ALIVE`, `ASSERT_WINNER`,
`ASSERT_GAME_OVER`). This is unrelated to `main.py`'s pixel-based
protocol — it addresses cells directly and is meant for concise,
readable end-to-end scenario tests, run via `tests/integration/test_text_scripts.py`.

## Package layout

```
kungfu_chess/
├── config.py           # shared constants (cell size, travel duration, board size, FPS)
├── model/               # Position, Piece, Color, PieceKind, PieceState, Board, GameState
├── rules/                # MoveRequest, per-piece PieceRule classes, RuleEngine, default_rule_engine()
├── realtime/            # IClock/SystemClock, Motion, JumpAction, RealTimeArbiter
├── engine/               # GameEngine, GameSnapshot
├── input/                # BoardMapper, Controller
└── io/                   # BoardParser, BoardPrinter

main.py                  # stdin/stdout command-driven entry point
texttests/                # .kfc script parser + runner (alternate test harness)
tests/
├── unit/                 # one test module per source module
├── integration/          # .kfc scenario scripts + runner test
└── test_main_pipeline.py # tests for main.py's stdin/stdout pipeline
```

## Design notes

- **Strategy pattern for piece movement** — each `PieceKind` has its own
  `PieceRule` class, and `default_rule_engine()` wires them into a
  `Dict[PieceKind, PieceRule]`. Adding a new piece type or house rule means
  adding one class, not editing a big conditional.
- **Chain of responsibility for legality** — `RuleEngine.can_move()` runs a
  list of small, single-purpose `MoveValidator`s in order and short-circuits
  on the first failure, keeping "does this piece exist", "is it idle", "is
  the destination legal", and "is the geometry legal" independently
  testable.
- **Clock injection** — `RealTimeArbiter` never reads the system clock
  itself; it takes an `IClock`. Production code uses `SystemClock`
  (`time.monotonic()`), while `main.py` and the test suites use a fake,
  manually-advanced clock. This makes all timing-dependent behavior
  (motion completion, jump landing) deterministic in tests.
- **Immutable value objects** — `Position`, `MoveRequest`, `Motion`,
  `JumpAction`, and `GameSnapshot` are frozen dataclasses. State only ever
  lives in `Piece.state`/`Piece.cell`, `Board`'s internal map, and
  `GameState`, so it's always clear what can and can't change out from
  under you.
- **Snapshot read-model** — nothing outside `engine/` mutates `GameState`
  directly; consumers (the `Controller`, `main.py`'s printer step) only see
  a `GameSnapshot`, keeping write access centralized in `GameEngine`.
- **Separation of legality vs. scheduling** — `rules/` decides *whether* a
  move is legal to start; `realtime/` decides *when* it actually takes
  effect and how conflicts at arrival are resolved. This split is what
  turns a normal chess rule set into a real-time game with almost no
  duplicated logic.

## Getting started

Requires Python 3.10+ (developed against 3.14) and `pytest` (+
`pytest-cov` for coverage).

```bash
pip install pytest pytest-cov
```

Run a scripted game from the command line:

```bash
python main.py < some_input.txt
```

or interactively, typing the `Board:`/`Commands:` protocol described above
and ending stdin (Ctrl+D / Ctrl+Z) when done.

## Running the tests

```bash
pytest
```

With coverage:

```bash
pytest --cov=kungfu_chess --cov=main --cov-report=term-missing --cov-report=html
```

- `tests/unit/` — one module per `kungfu_chess` source file.
- `tests/integration/` — runs the `.kfc` scenario scripts through
  `texttests/script_runner.py` against the real engine.
- `tests/test_main_pipeline.py` — exercises `main.py`'s stdin/stdout
  protocol end-to-end (parsing errors, moves, jumps, waits, malformed
  commands, and the `python main.py` script entry point).
