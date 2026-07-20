# Kung-Fu Chess UI — Architecture Deep Dive

This document explains **everything** under `ui/`: why it's shaped the way
it is, what each package does, how a single frame flows through the
system end to end, and the design decisions behind the less-obvious
parts. Read `ui/README.md` first if you just want to run it or check the
manual test checklist — this document is for understanding *how it works*.

## 1. The one rule everything else follows

`kungfu_chess/` is a finished, tested, **read-only** engine. Nothing under
`ui/` ever modifies it, reimplements its rules, or duplicates its timing
logic. `ui/` only ever:

- reads `GameEngine.get_snapshot()` to find out what's happening, and
- sends input through the engine's own `kungfu_chess.input.Controller`.

Every architectural choice below exists to make that boundary easy to
keep, and easy to *see* if it's ever violated.

## 2. The layers, and who may talk to whom

```
                          ui/main.py
                    (composition root — the
                     only file that knows every
                     layer at once)
                            |
        +-------------------+-------------------+
        |                   |                   |
   ui/input/           ui/animation/        ui/hud/
  MouseAdapter          SceneBuilder      Score/MoveLog/
        |               PieceAnimator      PlayerLabels/
        |               interpolator        HudRenderer/
        |               anim_clock/          GameOverBanner
        |               frame_clock              |
        |                   |                   |
        +-------------------+-------------------+
                            |
                     ui/rendering/
              Canvas protocol, CoordinateMapper,
              BoardRenderer, HighlightRenderer,
              CaptureFlash, JumpIndicator
                            |
                     ui/assets/
           piece_codes, asset_paths, SpriteLoader
                            |
                     ui/platform/
            Img, ImgFrameBuffer, ImgCanvas,
            OffscreenImgCanvas  <-- ONLY these
            files import cv2/numpy

                     ui/events/
        FrameSnapshot, diff_snapshots, EventBus
        (fed by main.py, consumed by ui/hud/)
```

The dependency direction is strict and one-way: `platform` knows nothing
about `rendering`; `rendering` knows nothing about `animation`, `hud`, or
`input`; only `main.py` (the composition root) is allowed to import from
every package and wire concrete objects together.

The single seam that makes this possible is **`Canvas`**
(`ui/rendering/canvas.py`) — a `Protocol`, not a concrete class. Every
package except `ui/platform/` depends on `Canvas`, never on `Img`/cv2
directly. That's what lets:

- `ui/platform/img_canvas.py` (`ImgCanvas`) drive a real OpenCV window,
- `ui/platform/offscreen_img_canvas.py` (`OffscreenImgCanvas`) render real
  pixels with no window (used by the headless PNG-proof scripts), and
- `ui/tests/support/fake_canvas.py` (`FakeCanvas`) just record draw calls
  for unit tests,

all sit behind the exact same interface, interchangeably, with zero
changes anywhere else.

## 3. Package-by-package

### `ui/platform/` — the only place that touches cv2

| File | Job |
|---|---|
| `img.py` | The `Img` class you provided (`read`, `draw_on`, `put_text`, `show`), adapted for a real-time loop: `show()` is non-blocking (`waitKey(wait_ms)` instead of `waitKey(0)` + `destroyAllWindows()`), plus `blank()`/`copy()`/`text_size()` additions a frame loop needs. |
| `img_frame_buffer.py` | Drawing logic shared by both canvases below (`begin_frame`, `blit`, `draw_text`, `compose`, `image_size`, `text_size`) — so they don't duplicate the same `Img` calls. |
| `img_canvas.py` | `ImgCanvas` — the interactive `Canvas`. Owns the OpenCV window and its mouse callback, translating raw cv2 mouse events into the clean `MouseEvent` type before anything else in `ui` sees them. |
| `offscreen_img_canvas.py` | `OffscreenImgCanvas` — a headless `Canvas`: real pixels, no window, plus `save(path)`. Used by every `ui/tests/manual/render_*.py` proof script. |

### `ui/rendering/` — the `Canvas` boundary + pure-ish drawing logic

| File | Job |
|---|---|
| `canvas.py` | The `Canvas` `Protocol` itself, plus `MouseEvent`/`MouseButton` and the opaque `ImageHandle` alias. This is the file every other package (except `platform`) imports instead of `Img`. |
| `coordinate_mapper.py` | Wraps the engine's own `BoardMapper`. Adds `sprite_anchor` (center + bottom-align a sprite in a cell) and `anchor_at` (same math, but for an arbitrary/interpolated pixel, not just a cell). |
| `board_renderer.py` | Purely mechanical: `draw(placements)` = begin_frame + blit each `(sprite, x, y)`. Doesn't know what a `Position` is anymore — whoever builds the placement list (`SceneBuilder`) decides where things go. |
| `highlight_renderer.py` | Translucent yellow overlay on `Controller.selected`. |
| `capture_flash.py` | Fading red overlay on a just-captured piece's square. Fed directly by the frame loop (`record(cell, now)` / `draw(now)`), not the event bus — it needs `now` for timing, and the bus is HUD-only by design. |
| `jump_indicator.py` | Translucent overlay on any piece currently `PieceState.JUMPING`. See §7 for why this isn't a cooldown timer. |

### `ui/assets/` — piece codes and sprite loading

| File | Job |
|---|---|
| `piece_codes.py` | Pure `(Color, PieceKind) -> "wP"`-style code, matching how `ui/assets/pieces_mine/` is actually laid out on disk (color letter then kind letter — same order as the engine's own board-text tokens). |
| `asset_paths.py` | Pure path resolution: `pieces_mine/<code>/states/<state>/{config.json,sprites/N.png}`, plus `BOARD_IMAGE`. |
| `sprite_loader.py` | `SpriteLoader.load(code, state)` reads `config.json` (fps/loop/next-state) and loads every frame, caching per `(code, state)`. Depends only on `Canvas.load_image` — never touches `cv2`/`Img` directly. |

### `ui/animation/` — timing and the motion/animation state machine

| File | Job |
|---|---|
| `anim_clock.py` | Pure: `frame_index(elapsed, frame_count)` / `is_finished(...)`. Loops forever or clamps to the last frame, depending on `is_loop`. |
| `frame_clock.py` | Paces/measures the render loop's own FPS. Deliberately never reads `snapshot.current_time` — a second, independent clock from the engine's (the "two clocks" rule, §6). |
| `interpolator.py` | `lerp_point(src, dst, progress)` — one straight-line lerp, nothing else. |
| `piece_animator.py` | The per-piece visual state machine (§5). |
| `scene_builder.py` | `SceneBuilder.build(snapshot, render_now)` — combines the animator, the interpolator, and the engine's live motion data into "what to draw and where" for one frame. This is the heart of Stage 6. |

### `ui/input/` — the one folder that talks to the engine's input adapter

| File | Job |
|---|---|
| `mouse_adapter.py` | `MouseAdapter.handle(events)` translates `MouseEvent`s into `Controller.on_click` / `Controller.on_jump` calls. No selection/move/jump logic lives here — the engine's own `Controller` already owns all of that; this is pure translation. |

### `ui/events/` — discrete-event diffing (Captured / Moved / Promoted / GameOver)

| File | Job |
|---|---|
| `frame_snapshot.py` | `capture_frame_snapshot(snapshot)` reduces a `GameSnapshot` to `{piece_id: (color, kind, state, cell)} + winner` — just enough to diff, nothing about interpolation. |
| `diff.py` | `diff_snapshots(previous, current)` — pure comparison. A piece_id vanishing → `PieceCaptured`. Its `cell` changing → `PieceMoved` (reliable because a piece's `cell` only changes at the exact tick its motion settles). Its `kind` changing → `PiecePromoted`. `winner` appearing → `GameOver`. |
| `event_bus.py` | `EventBus` — minimal Observer pub/sub. Publishers (the frame loop) don't know who's listening. |
| `events.py` | The four event dataclasses. |

### `ui/hud/` — sidebar panels, purely event-driven

| File | Job |
|---|---|
| `score_panel.py` | Tallies captured material per color from `PieceCaptured` events, using standard chess point values. **Display only** — never affects legality/outcome. |
| `move_log_panel.py` | Human-readable move/capture/promotion log (`"white pawn a2-a4"`), with simple algebraic-style cell labels. |
| `player_labels.py` | Tracks the winner from `GameOver`. |
| `hud_renderer.py` | Purely mechanical: reads the three panels above and calls `Canvas.draw_text`. Owns `SIDEBAR_WIDTH`. |
| `game_over_banner.py` | Dims the board and centers `"<COLOR> WINS"` once `PlayerLabels.winner` is set (uses `Canvas.text_size` for exact centering). |

### `ui/main.py` — the composition root

The **only** module allowed to know about every layer at once. Everything
is wired here via constructor injection — no module-level singletons,
nothing reaches for a global. See §4 for exactly what it does.

## 4. The composition root, end to end

`ui/main.py` has three phases:

1. **`build_engine()`** — parses the standard starting position through the
   engine's own `BoardParser`, then wires
   `GameState` → `RealTimeArbiter(SystemClock(), travel_duration=...)` →
   `GameEngine`. This is 100% engine-side; nothing here imports anything
   from `ui/rendering`, `ui/animation`, etc.

2. **`build_canvas()`** — the only function that knows the concrete
   `Canvas` is an `ImgCanvas`. Computes the window size from
   `DISPLAY_CELL_SIZE` (a UI-only constant, decoupled from the engine's
   `config.CELL_SIZE` — see §7) plus `SIDEBAR_WIDTH`.

3. **`run_game_loop(engine, canvas)`** — builds every collaborator (mapper,
   loader, renderer, animator/scene builder, HUD panels, event bus, the
   polish components) exactly once, then loops:

   ```
   while not canvas.should_close():
       now = render_clock.now()                 # wall-clock, for animation pacing
       frame_clock.tick(now)

       mouse_adapter.handle(canvas.poll_events())  # input -> Controller
       controller.on_tick()                        # -> engine.tick()
       snapshot = engine.get_snapshot()

       # diff -> events -> HUD panels + capture flash
       current_frame = capture_frame_snapshot(snapshot)
       events = diff_snapshots(previous_frame, current_frame)
       event_bus.publish(events)
       for e in events:
           if isinstance(e, PieceCaptured): capture_flash.record(e.cell, now)
       previous_frame = current_frame

       # decide what to draw and where (uses snapshot.current_time, not `now`,
       # for motion/jump interpolation -- see rule #2 below)
       placements = scene.build(snapshot, render_now=now)
       jumping_cells = [p.cell for p in snapshot.board.all_pieces()
                        if p.state == PieceState.JUMPING]

       renderer.draw(placements)
       highlight.draw(controller.selected)
       jump_indicator.draw(jumping_cells)
       capture_flash.draw(now)
       hud.draw(player_labels, score_panel, move_log_panel)
       game_over_banner.draw(player_labels)
       canvas.draw_text(fps_text, ...)              # shadow + white, for contrast
       canvas.present()

       sleep(remaining frame budget)                # cap to config.FPS
   ```

## 5. The per-piece animation state machine (`PieceAnimator`)

Each piece gets one `PieceAnimator`, created the first time its id is
seen. It tracks a **visual state** (`idle`, `move`, `jump`, `short_rest`,
`long_rest`) that is *not* the same thing as the engine's `PieceState`
(`IDLE`/`MOVING`/`JUMPING`/`CAPTURED`) — it's a finer-grained cosmetic
state driven by the actual sprite pack's `config.json` files.

Two ways a visual state changes:

- **Forced entry**: the engine enters `MOVING`/`JUMPING` → the animator
  snaps straight to `"move"`/`"jump"`, resetting its animation clock. This
  always wins.
- **Chained exit**: `"move"` and `"idle"` are `is_loop: true` in their
  `config.json` — by design, they last exactly as long as the engine keeps
  the piece in that state, and *never self-exhaust*. So the only way to
  leave `"move"` is noticing the engine already left `MOVING` while the
  animator is still parked there — treated as instant exhaustion, which
  kicks off `config.next_state_when_finished`. Non-looping states
  (`jump`, `short_rest`, `long_rest`) instead self-advance once their own
  frames run out.

The real chain, read directly off the shipped assets (not hardcoded):
`move → long_rest → idle` and `jump → short_rest → long_rest → idle`.

## 6. The two-clocks rule

There are deliberately **two independent clocks** in the running app:

1. **The engine's own clock** — a `SystemClock()` instance passed into
   `RealTimeArbiter`. Its only externally-visible trace is
   `snapshot.current_time`. **Motion and jump interpolation must use this
   value as `now`** (`motion.progress(snapshot.current_time)`), because
   that's the exact time basis the arbiter used to resolve collisions —
   using anything else risks rendering a different outcome than the one
   the engine actually decided (e.g. two pieces racing to the same
   square).

2. **The render clock** — a second, separate `SystemClock()` instance,
   used only for `FrameClock` (FPS pacing) and `PieceAnimator` (which
   sprite frame to show). Entirely cosmetic; nothing about it can change
   what the engine decides.

`SceneBuilder.build(snapshot, render_now)` takes both: `render_now` paces
animation, `snapshot.current_time` (read internally, off the `Motion`
objects) positions anything actually moving.

## 7. Things that look like bugs but are deliberate (and one that wasn't)

- **`JumpIndicator` is not a cooldown timer.** `RealTimeArbiter` tracks
  jump cooldown in a private `_jump_ready_at` dict that `GameSnapshot`
  never exposes. Re-deriving "seconds until this piece can jump again" in
  `ui/` would mean duplicating the engine's own timing logic — exactly
  what the architecture forbids. So the indicator only reacts to the
  observable `PieceState.JUMPING`, nothing more.

- **`ScorePanel`'s point values are not a rule.** They're a pure display
  convention (standard chess piece values) computed from already-resolved
  `PieceCaptured` events. They never feed back into legality, turns, or
  outcome.

- **`DISPLAY_CELL_SIZE` (in `main.py`) is not `kungfu_chess.config.CELL_SIZE`.**
  The engine has no concept of pixels — `config.CELL_SIZE` is only a
  default the reference `BoardMapper`/tests happen to use. The UI is free
  to render at any cell size, as long as it's threaded consistently
  through `BoardMapper`, `CoordinateMapper`, `SpriteLoader`, and the
  canvas/background dimensions. It was dropped from 100px/cell (an
  1100×800 window) to 70px/cell (860×560) purely because the original
  size didn't fit on some screens.

- **The one real bug found and fixed**: the adapted `Img.draw_on`, as
  given, mutated the *source sprite's own cached image* to drop its alpha
  channel whenever it was blitted onto a differently-shaped destination
  (e.g. a 4-channel sprite onto a 3-channel background) — and because
  `SpriteLoader` caches `Img` instances, that corruption was permanent:
  the first draw onto a mismatched background would silently break that
  sprite's transparency for every subsequent frame. Rewritten to blend
  per-channel without ever touching `self.img`'s data. Caught by the
  Stage 6 scripted-scenario PNG tool, which (unlike the board's own
  4-channel `board.png`) used a plain 3-channel background.

- **The FPS overlay was invisible on light squares.** Pure white text at a
  fixed screen position will occasionally land on a white board square —
  identical color, zero contrast. Root-caused by inspecting raw pixel
  values (a flat white row, no text-shaped variation) rather than
  guessing. Fixed with a one-pixel dark shadow drawn behind the white
  text.

## 8. Testing strategy

- **Pure-logic modules** (`anim_clock`, `frame_clock`, `interpolator`,
  `piece_codes`, `diff`, `event_bus`, `score_panel`, `move_log_panel`,
  `player_labels`) get real unit tests with no fakes needed.
- **Renderer-shaped modules** (`board_renderer`, `coordinate_mapper`,
  `highlight_renderer`, `capture_flash`, `jump_indicator`, `hud_renderer`,
  `game_over_banner`, `scene_builder`, `sprite_loader`, `mouse_adapter`)
  are tested against `FakeCanvas` (records draw calls) or the real engine
  wired with a `FakeClock` for deterministic timing — never against a
  real window.
- **`ui/tests/manual/render_*.py`** are headless proof scripts (real
  pixels via `OffscreenImgCanvas`, no window) for scenarios that are
  easier to *see* than to assert: the starting position, two rooks racing
  to swap squares (proving collision resolution renders exactly as the
  engine resolved it), a HUD-populated frame, and the three polish
  effects in isolation. Not pytest tests — run directly with
  `python -m ui.tests.manual.<name>`.
- **`ui/tests/support/fake_canvas.py`** is the shared `FakeCanvas` test
  double, plus `FakeImage`.

Rendering *feel* (does the window actually look good, does an animation
read as smooth) is checked by eye via `ui/README.md`'s manual checklist,
never asserted in a test.

## 9. Running it

```
python -m ui.main
```

Left-click selects/moves, right-click jumps, Esc or the window's close
button quits. See `ui/README.md` for the full manual checklist and the
headless verification commands.
