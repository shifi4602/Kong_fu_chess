# Mid-flight collisions — design doc

**Status: implemented.** This document explains the two collision rules you
described, whether they were implemented, and the architecture used to
implement the missing one — `Motion` and `RealTimeArbiter` now match this
design exactly (`kungfu_chess/realtime/motion.py`,
`kungfu_chess/realtime/real_time_arbiter.py`).

## The two rules

1. **Different colors, same square (in flight or not):** whichever piece
   arrives *later* captures whichever was there *earlier*. Applies whether
   one piece moved into a resting piece, or both were moving and crossed.
2. **Same color, "almost" meet:** if a piece's path would take it through a
   square that a friendly piece occupies at that moment (resting, or itself
   passing through), the piece that gets there *later* stops one square
   short instead of overlapping.

Your example: rook e1→e8, queen (same color) a4→h4. Their paths cross at e4.
The queen gets there first, so the rook — arriving at e4 later — never
actually reaches e4; it stops at e3.

## What's implemented today

Short answer: **rule 1 only partially, rule 2 not at all.**

- `Board._grid` (`kungfu_chess/model/board.py`) only ever stores *resting*
  positions. When a `Motion` starts, the piece stays recorded at `src` in
  the grid for the *entire* flight. It's moved to `dst` in exactly one
  place: `RealTimeArbiter._resolve_arrival` (`real_time_arbiter.py:87-112`),
  which fires only when `Motion.is_complete(now)` — i.e. only at the very
  end of the flight.
- `_resolve_arrival` checks *only* whatever is sitting in `board.get(dst)`.
  It has no idea what any other in-flight `Motion` is doing, and it never
  looks at any square except the final destination.
- `_is_path_clear` (`kungfu_chess/rules/piece_rules.py:7`) checks path
  blocking, but only against the *static* board at the moment a move is
  *requested*. It has no notion of time, so it can't know "the queen will be
  at e4 in one second."

Net effect: rule 1 happens to work **only when the collision square is
literally the destination of at least one of the pieces**, and only because
ticks are resolved in real completion-time order (so whichever motion
finishes later naturally sees the earlier arrival already sitting at `dst`).
The moment the shared square is an *intermediate* square for either piece —
your rook/queen example — nothing detects it at all. Rule 2 has no code path
whatsoever: once `start_motion` is called, nothing can ever stop a piece
before its declared `dst`.

## Why the fix generalizes cleanly

`duration = travel_duration * distance` (see `start_motion`) already means
every straight-line mover (king/queen/rook/bishop/pawn) moves at exactly one
square per `travel_duration` seconds. So a flight isn't really continuous —
it's a sequence of discrete square-to-square hops with known timestamps.
Knights are the one exception: `KnightRule` allows an (2,1) jump with no
path-clear check, so a knight's flight has no intermediate squares — it's
still just one hop straight to `dst`, exactly like today.

That means we can precompute, for every `Motion`, the exact list of squares
it will enter and the exact time it enters each one. Collision detection
becomes: process every "piece X enters square Y at time T" event across
*all* active motions, strictly in time order, and check what's already at Y
when each event fires. Whichever event for a given square fires **second**
is — by construction — the "later arrival," which is exactly rule 1. If it's
same-color, that mover stops a square short instead of taking the square —
rule 2. Same mechanism, one extra `if piece.color == occupant.color`.

This also unifies with, rather than replaces, what exists today:
`test_capture_on_arrival` and `test_friendly_landing_conflict_aborts_motion`
are just the special case where the "square" in question happens to be the
mover's own final `dst` and the other piece isn't moving. Those keep passing
unchanged.

## Data model changes

**`Motion`** gains a precomputed path:

```python
@dataclass(frozen=True)
class Motion:
    piece: Piece
    src: Position
    dst: Position
    path: Tuple[Position, ...]   # squares after src, in order; path[-1] == dst
    start_time: float
    duration: float              # unchanged: travel_duration * len(path)
```

`path` is built once in `start_motion`, using the same direction-stepping
logic `_is_path_clear` already uses (normalize `(dr, dc)` to -1/0/1, walk
from `src` to `dst`). For a knight, `path = (dst,)` — one entry, no
intermediate squares, matching current behavior exactly.

Square `k` (0-indexed into `path`) is entered at absolute time:

```
entry_time(k) = start_time + (k + 1) * (duration / len(path))
```

**`RealTimeArbiter`** gains a small per-piece progress table:

```python
self._motion_progress: Dict[str, int] = {}  # piece.id -> last settled index, -1 = still at src
```

(same pattern as the `_jump_ready_at` dict added for the jump cooldown.)

## The resolution algorithm

Each `tick(state)`, instead of only checking `motion.is_complete(now)`, the
arbiter does a **chronological merge** of "next pending entry" across all
active motions:

1. For every active motion, compute `target_index = min(len(path)-1, floor((now - start_time) / step_duration))`.
   If `target_index <= motion_progress[piece.id]`, this motion has nothing
   new to do this tick.
2. Among all motions that do have a next index to enter, pick the one whose
   `entry_time(current_index + 1)` is **smallest** (ties broken
   deterministically — see below). This is the next event to resolve.
3. Resolve that single square-entry:
   - **Square empty** → advance `motion_progress[piece.id]` by one. No board
     mutation needed — nothing else needs to know about a square the piece
     has already left behind. If this was the last square (`k == len(path)-1`),
     the motion is complete: `board.remove(src)`, `board.place(piece, dst)`,
     `piece.state = IDLE`, run `_maybe_promote` — i.e. today's arrival logic,
     unchanged.
   - **Square occupied by an enemy** (resting, jumping, *or* another
     in-flight motion that has already settled into that same square via an
     earlier-processed event) → capture it (`_capture`, unchanged), then
     **this mover's flight ends here**: `board.remove(src)`,
     `board.place(piece, path[k])`, `piece.state = IDLE`, drop all remaining
     path entries for this motion. Same as rule 1, now working for any
     square, not just `dst`.
   - **Square occupied by a friendly piece** → this mover is — by
     construction — the "later" one (its event fired second), so it stops
     **one square short**: `board.remove(src)`,
     `board.place(piece, path[k-1] if k > 0 else src)`, `piece.state = IDLE`.
     The friendly piece already there is untouched. This is rule 2, brand
     new.
4. Repeat from step 1 until no motion has a pending event with
   `entry_time <= now`.

Processing one event at a time (rather than jumping straight to
`target_index`) is what makes this correct regardless of tick granularity —
`main.py`'s script protocol can call `wait 5000` and then a single `tick()`,
which must still walk through every intermediate square in order rather than
only checking the final position at `now`.

### Tie-break rule (per your answer)

If two motions' next entry events land on the exact same square at the exact
same timestamp, the tie is broken **deterministically**: the motion with the
earlier `start_time` counts as "already there" (earlier); if `start_time` is
also equal, fall back to the order `start_motion` was called (a monotonic
counter assigned per motion at creation). This makes the outcome
reproducible and testable instead of depending on dict/list iteration order.

### No extra cooldown

Per your answer, a piece that stops early (captures mid-flight, or gets
stuck a square short) is treated **exactly like a normal arrival**: it goes
`IDLE` immediately and can be selected for its next move/jump right away —
no additional delay beyond what already exists (i.e. the jump cooldown
still applies only to jumps, untouched by this change).

### Interaction with jumping

A `JUMPING` piece already stays recorded at its own square in `Board` the
whole time it's airborne (jumping never touches the grid). Because the new
resolver checks `board.get(square)` at every step — not just at `dst` — a
mover whose *path* merely passes through a square where an enemy is
currently jumping now gets captured by the jump-defense rule mid-flight too,
for free, using the exact same `occupant.state == JUMPING` check
`_resolve_arrival` already has today.

## Worked example (your rook/queen scenario)

`travel_duration = 1.0s`. Rook e1→e8 (distance 7, `path` = e2..e8),
queen a4→h4 (distance 4, `path` = b4..h4), both start at `t = 0`.

- Rook enters e4 (its 4th square, k=3) at `t = 4.0`.
- Queen enters e4 (her 4th square, k=3) at `t = 4.0`.

That's an exact tie on the same square at the same time → deterministic
tie-break by `start_time` (equal) → by creation order. If the rook's motion
was `start_motion`'d first, the queen is considered to have "arrived
first" logically... — **but** note this exact-tie case only arises if both
started at literally the same instant. In your description the queen's move
is issued *while the rook is already moving*, e.g. rook starts at `t=0`,
queen starts at `t=1`:

- Rook enters e4 at `t = 4.0` (its k=3 event).
- Queen, starting a `t=1`, enters e4 at `t = 1 + 4*1.0 = 5.0`.

Rook's event (t=4.0) resolves first: e4 is empty, rook advances normally
through it toward e8. Then at `t=5.0`, queen's event fires: e4 is empty
again (rook already left) — no collision either. For the rook to actually
get stuck at e3, the **queen's** entry into e4 must happen at or before
`t=4.0`, i.e. the queen must start no later than `t=0.0` (since her e4 entry
is her 4th step: `queen_start + 4.0 <= 4.0`). With the queen starting at
`t=0` (same time as the rook), her e4 event and the rook's tie exactly —
resolved by creation order as above. If the queen instead started slightly
*before* the rook (e.g. `t=-0.5`), her e4 entry event (`t=3.5`) fires before
the rook's (`t=4.0`) — she settles e4 momentarily "in transit" (advances
through, since nothing is there yet), and when the rook's event fires at
`t=4.0`, e4 is empty again because the queen already moved past it. This
matches real intuition: two pieces only actually collide if their time
windows *at that square* genuinely overlap — which, since each occupies a
square for one full `travel_duration` before moving to the next, means the
rook needs to enter e4 within the same `travel_duration` window the queen
occupies it. This is a natural consequence of the per-square timing model,
not a special case to code — it falls out of comparing `entry_time` values.

## Compatibility with existing tests

Most existing tests kept passing unchanged, since they only ever exercised
the `k == len(path)-1` (final-arrival) case, which behaves identically to
before. Two did not, and were deliberately updated because the old
expectation was exactly the incidental behavior this feature replaces:

- `test_friendly_landing_conflict_aborts_motion` → renamed
  `test_friendly_landing_conflict_stops_one_square_short`. Previously, a
  rook blocked by a friendly piece sitting on its destination reverted all
  the way back to `src`. Under rule 2, it now stops **one square short of
  the block** instead — for `(0,0)→(0,3)` blocked at `(0,3)`, the rook now
  ends at `(0,2)`, not `(0,0)`.
- `test_captured_piece_in_flight_motion_does_not_resurrect` → renamed
  `test_swapping_enemies_collide_and_capture_at_crossing_square`. Two
  enemies swapping squares along the same line now correctly collide and
  resolve the capture at the **midpoint crossing square**, not at either
  one's original destination — this is the flagship scenario the whole
  feature exists for.

`Motion` also gained two new required fields (`path`, `sequence`), so the
three tests in `tests/unit/test_real_time_arbiter.py` that construct
`Motion(...)` directly (`test_motion_progress_*`) needed those arguments
added — no behavior change there, just satisfying the new dataclass shape.

Two lines from the first implementation draft turned out to be
unreachable defensive guards once the algorithm's invariants were worked
through (a `steps == 0` case in `_build_path`, and a "motion already past
its own path length" guard in `_earliest_pending_motion`) — both were
removed rather than covered with dead-code tests, per this repo's
don't-guard-against-impossible-inputs convention. `Motion.is_complete` also
became fully unused once entry-time-based scheduling replaced it, so it was
deleted rather than left dangling.

One correctness subtlety surfaced during implementation: the internal
per-motion progress table is keyed by `id(motion)` (Python object identity),
not `piece.id` (the domain string field) like the jump-cooldown table is.
The test fixtures' `_piece()` helper hands out the same hardcoded `id='t'`
to every piece, so keying by the domain id would silently collide the
instant two pieces are moving at once — exactly the case this feature has
to get right. `_resident_at`'s "is this piece the mover itself" check was
made identity-based (`is`) for the same reason.

## Tests added

All added to `tests/unit/test_real_time_arbiter.py`, under
`# --- Mid-flight collisions ---`:

- `test_mid_path_friendly_block_stops_one_square_short` — rook flies
  through a square a same-color piece is *resting* on (mid-path, not
  `dst`) → stops one square short.
- `test_mid_path_enemy_is_captured_and_motion_ends_there` — rook flies
  through a square an enemy is *resting* on (mid-path) → captures it there
  and stops; never reaches the original `dst`.
- `test_coarse_tick_after_large_wait_still_stops_at_mid_path_block` — a
  single huge `clock.advance()` + one `tick()` still stops at the correct
  intermediate square rather than skipping straight to a time-implied final
  index.
- `test_crossing_paths_same_color_later_mover_stops_short` /
  `test_crossing_paths_different_color_later_mover_captures` — two motions
  (staggered start times, not a tie) whose paths cross at a shared square →
  the one that gets there later stops short (same color) or captures
  (different color); the earlier one completes its own move normally.
- `test_exact_tie_broken_by_creation_order` — two same-color motions
  scheduled to enter the same square at the exact same instant → resolved
  deterministically by which `start_motion` call happened first.
- `test_pawn_mid_path_capture_regression` — pawn diagonal capture
  (`path` length always 1) behaves exactly as before.
- `test_knight_motion_has_no_intermediate_squares` — a knight's `(2,1)`
  jump still has `path = (dst,)`, one hop, same duration as before.
- `test_jump_defense_triggers_at_mid_path_square` — a mover whose path
  merely passes through a square where an enemy is currently `JUMPING` gets
  captured by the jump-defense rule mid-flight, not just at final arrival.

## Known, deliberate edge cases worth remembering

- The tie-break is by motion creation order — deterministic, but arbitrary
  from a "who's actually right" standpoint for a genuine exact tie. This
  matches what you asked for; flagging only so it's a known, documented
  choice rather than an accident.
- Nothing about board rendering (`BoardPrinter`) needed to change — the
  board only ever shows resting positions, same as before; in-flight pieces
  are still only visible via `GameSnapshot.motions`, unchanged.

## Future work: performance at larger scale (not implemented)

`_resolve_motions` currently has two independent `O(N)` linear scans in its
hot path, where `N` is the number of active motions:

1. `_earliest_pending_motion` rescans every active motion, on every single
   resolved event, to find the next one chronologically. A tick that
   resolves `E` events costs `O(E·N)`.
2. `_resident_at` also rescans every other active motion, per event, to
   check whether it currently occupies the target cell.

For this project — a chess board, max 32 pieces — this is a non-issue,
which is why the simple linear scan was chosen over a more complex
structure. If this arbiter is ever reused for a scenario with hundreds or
thousands of concurrently-moving entities, both scans would need to be
replaced together (fixing only one leaves the other dominating):

- A min-heap of `(entry_time, sequence)` per motion, populated in full at
  `start_motion` time (every entry time for a motion's whole path is fixed
  at creation, so the entire path can be pushed up front, not just the next
  step). Needs **lazy deletion**: when a motion is cancelled mid-tick
  (captured or blocked), its still-queued future heap entries go stale —
  check "is this still the motion's next expected index and is it still
  active" on pop, and discard if not.
- An auxiliary `cell → (piece, motion)` occupancy index for in-flight
  movers, updated in `O(1)` as each motion advances a square. This is what
  actually fixes `_resident_at` — the heap alone does not, since it only
  speeds up picking the next event, not the residency check.

Together these would bring a tick from roughly `O(E·N)` down to
`O(E log N)`. Flagging this now so it isn't forgotten if piece/entity counts
ever grow beyond chess scale — not something to build today.
