# Kung-Fu Chess UI

A graphical front end for the `kungfu_chess` engine. `kungfu_chess/` is
never modified -- this package is a pure consumer of
`GameEngine.get_snapshot()` and drives input through the engine's own
`kungfu_chess.input.Controller`.

## Running it

```
python -m ui.main
```

Opens a window (board + sidebar). Left-click selects/moves a piece,
right-click jumps a selected/idle piece. Press **Esc** or close the window
to quit.

## Architecture

| Package | Responsibility | May import backend (cv2/Img)? |
|---|---|---|
| `ui/platform/` | `Img` wrapper, `ImgCanvas` (live window), `OffscreenImgCanvas` (headless) | Yes -- the only package that may |
| `ui/rendering/` | `Canvas` protocol, `CoordinateMapper`, `BoardRenderer`, `HighlightRenderer`, `CaptureFlash`, `JumpIndicator` | No |
| `ui/assets/` | Piece-code mapping, asset path resolution, `SpriteLoader` | No |
| `ui/animation/` | `AnimClock`, `FrameClock`, `PieceAnimator`, interpolation, `SceneBuilder` | No |
| `ui/input/` | `MouseAdapter` -- the only place that calls `kungfu_chess.input.Controller` | No |
| `ui/events/` | `FrameSnapshot`, pure `diff_snapshots`, `EventBus` | No |
| `ui/hud/` | `ScorePanel`, `MoveLogPanel`, `PlayerLabels`, `HudRenderer`, `GameOverBanner` | No |
| `ui/main.py` | Composition root -- the only module that wires every layer together | No (delegates to `ui/platform`) |

Every module outside `ui/platform/` depends only on the `Canvas` protocol
(`ui/rendering/canvas.py`) -- never on `Img`/cv2 directly. Tests substitute
`FakeCanvas` (records draw calls) or `OffscreenImgCanvas` (real pixels, no
window) for the same reason.

## Manual verification checklist

Automated coverage lives in `ui/tests/unit`. The items below are
inherently about *feel* and are checked by eye, not asserted:

- [ ] `python -m ui.main` opens a window sized board + sidebar; closes
      cleanly on Esc or the window's close button.
- [ ] Every piece's idle sprite renders in the right cell, right color.
- [ ] Idle sprites subtly animate (they're a 4-5 frame loop, not static).
- [ ] FPS counter (top-left of the board) reads close to 60.
- [ ] Clicking an idle piece highlights its cell; clicking again deselects.
- [ ] Clicking a highlighted piece then an empty square slides it there in
      real time (not an instant jump-cut).
- [ ] Right-clicking an idle piece plays its jump animation and shows the
      blue jump-indicator overlay while airborne.
- [ ] Two pieces moved toward the same square resolve the same way
      visually as the engine resolves them (whichever one the engine
      settles at the square is the one still there after).
- [ ] A capture shows a brief red flash on the captured piece's square.
- [ ] The sidebar's Score and Moves update live as pieces move/capture.
- [ ] Capturing a king dims the board and shows "<COLOR> WINS" centered
      over it.

## Headless / scripted verification (no display needed)

- `python -m ui.tests.manual.render_static_board [out.png]` -- starting
  position, all idle sprites.
- `python -m ui.tests.manual.render_motion_scenario [out_dir]` -- two rooks
  racing to swap squares; dumps start / mid-flight / resolved frames.
- `python -m ui.tests.manual.render_hud_scenario [out.png]` -- replays a
  capture and renders the sidebar with live score + move log.
- `python -m ui.tests.manual.render_polish_scenarios [out_dir]` -- capture
  flash, jump indicator, and the game-over banner, each in isolation.

## Test gates

```
python -m pytest ui/tests/unit -v   # pure-logic + FakeCanvas renderer tests
python -m pytest                    # full repo, including the untouched engine suite
```
