# SQLite Persistence — Architecture Plan

This is a planning document, not yet implemented. It designs the real
persistence layer for `kungfu_chess`'s server, replacing
`server/persistence/user_repository.py`'s `InMemoryUserRepository`
placeholder with SQLite-backed storage.

This advances the server from **stage 1** to **stage 3** of the roadmap in
`docs/SERVER_PLAN.md` §15 ("Password + SQLite `UserRepository` impl, ELO
field"). It also resolves the "not-yet-designed stage-3 result-recording
step" `docs/SERVER_PLAN.md` §9.6 explicitly flags as a gap. It does **not**
implement stage 4 (ELO-window matchmaking) — ratings get stored and
updated here, but nothing yet *matches* players by rating. That stays a
`MatchmakingStrategy` swap on top of this, unchanged, per the existing
Strategy pattern (`docs/SERVER_PLAN.md` §6).

## 1. What SQLite is — and isn't — for

**SQLite stores accounts and finished-game history. It never stores live
game state.** `GameEngine`/`GameSession`/`RealTimeArbiter` keep running
entirely in memory, exactly as `docs/SERVER_PLAN.md` designed — a
`GameSession` is still just a Python object in `SessionRegistry`, ticked
by `advance(now_ms)`. Two consequences follow directly from that split:

- A server restart loses all in-progress games. That's already true today
  (nothing persists a `GameSnapshot`) and this plan doesn't change it —
  adding mid-game persistence/resume is a separate, much larger feature
  (would need to serialize `Motion`/`JumpAction` timing state) and isn't
  requested here.
- Every database write in this design happens at a **boundary**: account
  creation/login (before a game exists) and game-result recording (after
  a game ends). Nothing on the hot path — `GameSession.advance()`,
  `_drain_pending()`, the move/jump ownership check — ever touches the
  database. That's what keeps `docs/SERVER_PLAN.md` §9's sync-core
  design (`advance(now_ms)` testable with bare integers, no I/O) intact.

## 2. What gets persisted

Two tables, both created idempotently at startup (§6):

```sql
-- server/persistence/schema.sql

CREATE TABLE IF NOT EXISTS accounts (
    username        TEXT PRIMARY KEY,
    password_hash   BLOB NOT NULL,
    password_salt   BLOB NOT NULL,
    elo_rating      INTEGER NOT NULL DEFAULT 1200,
    created_at_utc  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE TABLE IF NOT EXISTS games (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id           TEXT NOT NULL UNIQUE,
    white_username       TEXT NOT NULL REFERENCES accounts(username),
    black_username       TEXT NOT NULL REFERENCES accounts(username),
    winner_color         TEXT NOT NULL CHECK (winner_color IN ('white', 'black')),
    white_rating_before  INTEGER NOT NULL,
    black_rating_before  INTEGER NOT NULL,
    white_rating_after   INTEGER NOT NULL,
    black_rating_after   INTEGER NOT NULL,
    recorded_at_utc      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_games_white ON games(white_username);
CREATE INDEX IF NOT EXISTS idx_games_black ON games(black_username);
```

Design choices worth calling out:

- **`games.session_id` is `UNIQUE`.** `GameOverEvent` fires exactly once
  per session (`docs/SERVER_PLAN.md` §9.5's edge-trigger), but the
  `UNIQUE` constraint is defense in depth — if a future change ever
  causes a duplicate recording attempt, SQLite rejects the second insert
  instead of silently double-counting a rating change.
- **Both pre- and post-game ratings are stored on the `games` row**, not
  just the delta. That makes `games` a self-contained audit log — you can
  reconstruct a player's rating history by querying `games` alone,
  without replaying ELO math or depending on `accounts.elo_rating` (which
  only ever holds the *current* value) still matching what it was at the
  time.
- **No `password` column, ever.** Only `password_hash` (a digest) and
  `password_salt` (random, per-account) are stored — see §7.
- **No table stores in-progress game state.** Consistent with §1.

## 3. Package layout additions

```
server/
  persistence/
    __init__.py
    models.py                  # Account — a frozen dataclass, the repository's return type
    user_repository.py         # UserRepository Protocol (extended) + InMemoryUserRepository (tests)
    sqlite_user_repository.py  # SqliteUserRepository — the real implementation
    game_repository.py         # GameRepository Protocol + InMemoryGameRepository (tests)
    sqlite_game_repository.py  # SqliteGameRepository — the real implementation
    db.py                       # connect(path) -> sqlite3.Connection, apply_schema(conn)
    schema.sql                  # the DDL in §2, loaded and executed by db.py
    elo.py                       # compute_new_ratings(...) — a pure function, no I/O

  results/
    __init__.py
    game_result_recorder.py    # subscribes to OUTBOUND, records finished games (§8)
```

`persistence/` already exists and is already the bottom layer in
`.importlinter`'s `server-layers` contract
(`server.protocol | server.persistence`) — every new file above lives
inside that same layer, importable by everything above it, importing
nothing above itself. No `.importlinter` changes are needed for it.

`results/` is new. It needs **both** `session/` (to look up which
players were in a finished session) **and** `persistence/` (to record
the result) — the same shape `logging_/activity_logger.py` already has
(needs `handlers/`'s `InboundMessage` *and* `transport/`'s
`OutboundMessage`). Like `logging_/`, `results/` sits outside the five
named layers in the `server-layers` contract, so it's free to depend on
both without a contract change — see §9 for exactly what it imports.

## 4. `Account` and the extended `UserRepository` protocol

The current `UserRepository` Protocol is a placeholder:

```python
# server/persistence/user_repository.py — today
class UserRepository(Protocol):
    def register(self, username: str) -> None: ...
```

That's not enough once passwords and ratings exist. The replacement:

```python
# server/persistence/models.py
@dataclass(frozen=True)
class Account:
    username: str
    elo_rating: int
    created_at_utc: str


# server/persistence/user_repository.py
class UsernameTakenError(Exception):
    """Raised by create_account() when the username already exists."""


class InvalidCredentialsError(Exception):
    """Raised by authenticate() when the username doesn't exist or the
    password doesn't match — one error, not two, so a client (or an
    attacker) can't distinguish "wrong password" from "no such user" by
    catching a different exception type."""


class UserRepository(Protocol):
    def create_account(self, username: str, password: str) -> Account: ...
    def authenticate(self, username: str, password: str) -> Account: ...
    def get(self, username: str) -> Optional[Account]: ...
    def update_rating(self, username: str, new_rating: int) -> None: ...
```

`InMemoryUserRepository` gets a matching rewrite (still zero I/O, still
what unit tests for `JoinHandler`-adjacent logic use when they don't
specifically want to exercise SQLite) so the Protocol has two
implementations from day one, per the existing Repository-pattern intent
in `docs/SERVER_PLAN.md` §6.

`GameRepository` is a new, parallel Protocol:

```python
# server/persistence/game_repository.py
class GameRepository(Protocol):
    def record_game(
        self,
        session_id: str,
        white_username: str,
        black_username: str,
        winner_color: Color,
        white_rating_before: int,
        black_rating_before: int,
        white_rating_after: int,
        black_rating_after: int,
    ) -> None: ...
```

## 5. `SqliteUserRepository` / `SqliteGameRepository`

Both take an already-open `sqlite3.Connection` in their constructor —
they don't open their own connection. `server/persistence/db.py` is the
one place that knows the file path, `PRAGMA`s, and schema bootstrapping
(§6); the two repositories are pure query/mutation logic on top of a
connection someone else handed them. That mirrors how `GameSessionFactory`
doesn't construct its own `ManualClock`-independent state — connection
lifetime is a composition-root concern (`server/main.py`), not a
repository concern.

```python
# server/persistence/sqlite_user_repository.py (sketch)
class SqliteUserRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def create_account(self, username: str, password: str) -> Account:
        if self.get(username) is not None:
            raise UsernameTakenError(username)
        salt = secrets.token_bytes(16)
        password_hash = _hash_password(password, salt)
        with self._conn:
            self._conn.execute(
                "INSERT INTO accounts (username, password_hash, password_salt) VALUES (?, ?, ?)",
                (username, password_hash, salt),
            )
        return self.get(username)

    def authenticate(self, username: str, password: str) -> Account:
        row = self._conn.execute(
            "SELECT password_hash, password_salt FROM accounts WHERE username = ?", (username,)
        ).fetchone()
        if row is None or _hash_password(password, row["password_salt"]) != row["password_hash"]:
            raise InvalidCredentialsError(username)
        return self.get(username)

    def get(self, username: str) -> Optional[Account]:
        row = self._conn.execute(
            "SELECT username, elo_rating, created_at_utc FROM accounts WHERE username = ?",
            (username,),
        ).fetchone()
        return None if row is None else Account(**row)

    def update_rating(self, username: str, new_rating: int) -> None:
        with self._conn:
            self._conn.execute(
                "UPDATE accounts SET elo_rating = ? WHERE username = ?", (new_rating, username)
            )
```

`with self._conn:` uses `sqlite3`'s built-in transaction context manager
(commits on success, rolls back on exception) — no separate
transaction-management code needed. `_hash_password` uses constant-time
comparison (`hmac.compare_digest`) for the digest check, not `==` — see
§7.

`SqliteGameRepository.record_game(...)` is a single parameterized
`INSERT` into `games`, wrapped the same way.

## 6. Connection management: one connection, WAL mode, sync stdlib

**One `sqlite3.Connection`, opened once in `server/main.py` (the
composition root), handed to both repositories.** No connection pool.
Reasoning:

- The server is single-threaded `asyncio` (`docs/SERVER_PLAN.md` §9.2's
  sync-core design) — there is no concurrent-thread access to guard
  against, so a connection pool would solve a problem this architecture
  doesn't have.
- SQLite's Python driver (`sqlite3`, stdlib — no new dependency) is
  synchronous/blocking. Every call above happens at a **boundary** (§1):
  account creation/login during `JoinHandler.handle()`, rating updates
  during `GameResultRecorder` (§8) — never inside `GameSession.advance()`
  or the scheduler's tick loop. A local SQLite file with WAL mode
  (below) resolves single-row reads/writes in well under a millisecond,
  so the brief block of the event loop during that call is negligible at
  this deployment's scale (a local/classroom server, same scale
  `docs/SERVER_PLAN.md` §16 already assumes for its cleartext-`ws://`
  trade-off).
- **If this ever needs to change** — a busier deployment where blocking
  the loop for sub-millisecond calls starts to matter — the fix is
  localized: wrap each repository call at its call site in
  `asyncio.to_thread(...)`, without touching the repository
  implementations or their Protocol signatures. Noted here as the
  documented escape hatch, not built now, per the same "don't build it
  until there's a measured need" discipline `docs/SERVER_PLAN.md` §16
  already applies to its own tuning constants.

`db.py`:

```python
# server/persistence/db.py
import sqlite3
from importlib import resources


def connect(path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA foreign_keys = ON")
    apply_schema(conn)
    return conn


def apply_schema(conn: sqlite3.Connection) -> None:
    schema_sql = resources.files("server.persistence").joinpath("schema.sql").read_text()
    with conn:
        conn.executescript(schema_sql)
```

`conn.row_factory = sqlite3.Row` is what lets `Account(**row)` work
directly in §5 — `sqlite3.Row` supports `dict`-style unpacking by column
name, so repository code never hand-indexes tuple positions (`row[0]`,
`row[1]`, ...), which would silently break the moment a column is added
or reordered.

**Schema management stays intentionally simple: idempotent
`CREATE TABLE IF NOT EXISTS` run at every startup, no migration
framework.** At this project's scale (two tables, a single deployment,
no production data to preserve across incompatible schema changes yet),
introducing Alembic-style versioned migrations now would be solving a
problem that doesn't exist yet. If the schema needs a breaking change
later (e.g. a new non-nullable column on `accounts`), that's the trigger
to introduce a real migration tool — not a reason to build one
speculatively today.

`:memory:` as the `path` argument is exactly how tests get a fresh,
isolated database per test (§10) — `sqlite3.connect(":memory:")` is a
completely ordinary call to the same `connect()` function, no test-only
code path needed in `db.py` itself.

## 7. Password hashing

`hashlib.pbkdf2_hmac("sha256", password.encode(), salt, iterations=200_000)`
— stdlib only, no new dependency (`bcrypt`/`argon2` are cryptographically
stronger but would be the project's third external dependency after
`websockets` and `import-linter`, for a local/classroom deployment that
`docs/SERVER_PLAN.md` §16 already documents as accepting cleartext
`ws://` transport). This is recorded as a known limitation, the same way
§16 already records its cleartext-transport trade-off — **if this server
ever moves beyond localhost/classroom use, both the transport (`wss://`)
and the hashing (`argon2`) should be revisited together**, not
separately.

- `password_salt`: 16 random bytes from `secrets.token_bytes(16)` per
  account, generated once at `create_account()` time, stored alongside
  the hash. Never reused across accounts.
- Comparison uses `hmac.compare_digest(computed, stored)`, not `==` —
  constant-time, so a timing attack can't leak how many leading bytes of
  the hash matched.
- The plaintext `password` string only ever exists as a local variable
  inside `create_account()`/`authenticate()`'s call stack — it's never
  logged (`logging_/activity_logger.py` logs `Command`s, and
  `JoinCommand`/a future login command would need its password field
  scrubbed before logging — see §11) and never stored.

## 8. Wire protocol changes this requires

This plan's scope is the persistence layer, but a password can't reach
`SqliteUserRepository.authenticate()` without a wire-protocol change —
named here so it isn't discovered as a surprise gap during
implementation, same discipline as `docs/SERVER_PLAN.md` §16's
"known limitations" list.

- `JoinCommand` (`server/protocol/commands.py`) needs a `password: str`
  field alongside `username`.
- `ErrorCode` (`server/protocol/errors.py`) needs one new member —
  `INVALID_CREDENTIALS` — for `authenticate()` failures, following the
  same closed-enum discipline `docs/SERVER_PLAN.md` §5 uses for the rest
  of the set.
- `JoinHandler.handle()` calls `authenticate()` (existing account) or
  `create_account()` (new username) instead of today's placeholder
  `users.register(cmd.username)`, and publishes
  `ErrorEvent(reason=ErrorCode.INVALID_CREDENTIALS)` unicast on failure
  instead of proceeding to `Lobby.join(...)`.
- This is additive to the existing closed record set (`codec.py`'s type
  registry, per `docs/SERVER_PLAN.md` §5, is exactly the seam designed
  to extend without touching transport or session code) — no other file
  in `transport/`, `session/`, or `bus/` needs to change for this.

This document doesn't design the full login UX (e.g. whether a bad
password should look identical to "no such account" in the *client's*
UI, not just the wire error code) — that's a `ui/net/` concern per
`docs/SERVER_PLAN.md` §17's open question #2, out of scope here.

## 9. Recording finished games: `GameResultRecorder`

`GameOverEvent` (`server/protocol/events.py`) carries only
`trace_id` and `winner: Color` — no usernames, no session id, by design
(`docs/SERVER_PLAN.md` §5's wire records are deliberately minimal). The
routing envelope `OutboundMessage` (`server/transport/outbound_message.py`)
already carries `session_id` alongside every event `GameSession`
publishes — that's the hook this component uses instead of adding
anything to the wire format.

```python
# server/results/game_result_recorder.py (sketch)
class GameResultRecorder:
    def __init__(
        self,
        bus: EventBus,
        registry: SessionRegistry,
        users: UserRepository,
        games: GameRepository,
    ) -> None:
        self._registry = registry
        self._users = users
        self._games = games
        bus.subscribe(Topics.OUTBOUND, self.handle_outbound)

    def handle_outbound(self, message: OutboundMessage) -> None:
        if not isinstance(message.event, GameOverEvent) or message.session_id is None:
            return
        session = self._registry.get(message.session_id)
        if session is None:
            return  # already reaped; shouldn't happen given §9.6's grace period, but never crash on it

        players = [session.player_for(cid) for cid in session.player_ids]
        white = next(p for p in players if p.color == Color.WHITE)
        black = next(p for p in players if p.color == Color.BLACK)
        white_account = self._users.get(white.username)
        black_account = self._users.get(black.username)

        white_after, black_after = compute_new_ratings(
            white_rating=white_account.elo_rating,
            black_rating=black_account.elo_rating,
            winner_color=message.event.winner,
        )

        self._games.record_game(
            session_id=message.session_id,
            white_username=white.username,
            black_username=black.username,
            winner_color=message.event.winner,
            white_rating_before=white_account.elo_rating,
            black_rating_before=black_account.elo_rating,
            white_rating_after=white_after,
            black_rating_after=black_after,
        )
        self._users.update_rating(white.username, white_after)
        self._users.update_rating(black.username, black_after)
```

Why this timing is safe: `GameOverEvent` is edge-triggered exactly once
per session (`docs/SERVER_PLAN.md` §9.5), fired from inside `advance()`
*before* that session becomes eligible for reaping
(`session_ttl_after_game_over_ms` only starts counting down after
`GameOverEvent` already went out — §9.6). So `SessionRegistry.get(...)`
is guaranteed to still find the session at the moment this handler runs;
the `if session is None: return` guard is defensive, not load-bearing.

`GameSession.player_for()`/`.player_ids` (already exist — added so
`handlers/move_handler.py`/`jump_handler.py`/`heartbeat_handler.py` and
`SessionRegistry`'s connection-id index could look players up) give this
component everything it needs — no new accessor required on
`GameSession` itself.

`server/persistence/elo.py`'s `compute_new_ratings(...)` is a small,
pure function (standard ELO formula, fixed K-factor — a `ServerConfig`
field, `elo_k_factor: int = 32`, so it's tunable without a code change,
consistent with every other tunable in `docs/SERVER_PLAN.md` §12) — unit
tested in complete isolation from the database, the bus, or sessions.

## 10. Testing strategy

Mirrors `docs/SERVER_PLAN.md` §13's existing discipline:

- **`elo.py`**: pure function, plain `assert`-based unit tests — a 1200
  vs 1200 win nets +16/-16 at K=32, a big underdog win nets more, ratings
  never go negative, etc.
- **`SqliteUserRepository`/`SqliteGameRepository`**: tested against a
  real `sqlite3.connect(":memory:")` database via `db.connect(":memory:")`
  — not mocked. This is *more* trustworthy than a `Fake*` double here,
  the same reasoning `docs/SERVER_PLAN.md` §13 uses for its own
  transport `FakeConnection`: a fake would encode assumptions about
  SQLite's behavior that could quietly drift from the truth, whereas
  `:memory:` runs the exact same query/transaction code the file-backed
  database runs, just against a database that vanishes at test-process
  exit — fast (no disk I/O) and hermetic (no shared state between
  tests). Covers: duplicate `create_account()` raises
  `UsernameTakenError`; `authenticate()` with a wrong password (or
  nonexistent user) raises `InvalidCredentialsError` in both cases
  identically; `update_rating()` persists across a fresh `get()`; `games`
  round-trips every column including the `UNIQUE(session_id)` constraint
  rejecting a duplicate insert.
- **`GameResultRecorder`**: constructed with a real `EventBus`, a real
  `SessionRegistry` holding one `GameSession` built via
  `GameSessionFactory` (exactly like `tests/server/test_game_session.py`
  already does), and `InMemoryUserRepository`/`InMemoryGameRepository`
  for the persistence side (isolating "did the recorder compute and call
  correctly" from "does SQLite work" — the latter is `SqliteUserRepository`'s
  own test's job). Asserts: a `GameOverEvent` triggers exactly one
  `record_game()` call with both usernames and correct before/after
  ratings; an `OutboundMessage` with `session_id=None` (e.g. a
  `HeartbeatEvent`) is ignored; a `StateEvent` broadcast is ignored.
- **`db.py`**: `connect(":memory:")` twice in the same test produces two
  independent databases (a common `:memory:` footgun — different
  connections to `:memory:` are *not* the same database unless you
  explicitly share a URI-mode connection); `apply_schema()` run twice
  against the same connection doesn't raise (proves `IF NOT EXISTS`
  idempotency, which the whole "no migration framework yet" decision in
  §6 depends on).
- **Password hashing**: same password + same salt → same hash
  (deterministic); same password + different salt → different hash (the
  salt is actually being used); wrong password → `authenticate()` raises,
  never silently returns an `Account`.

## 11. `server/main.py` wiring changes

```python
# server/main.py — additions to build_server()
db_conn = db.connect(config.database_path)   # new ServerConfig field, §12
users = SqliteUserRepository(db_conn)         # replaces InMemoryUserRepository()
games = SqliteGameRepository(db_conn)

# ... existing dispatcher/lobby/broadcaster wiring, unchanged ...

GameResultRecorder(bus, registry, users, games)  # subscribes itself, like ActivityLogger
```

`ServerConfig` (`server/config.py`) gains one field:
`database_path: str = "kungfu_chess.db"`, validated non-empty in
`__post_init__`, overridable via `SERVER_DATABASE_PATH` in `from_env()`
— same pattern every other config field already follows.

Nothing under `handlers/`, `session/`, `transport/`, or `bus/` changes
except `JoinHandler` (§8) — the entire point of the Repository pattern
being in place since stage 1 (`docs/SERVER_PLAN.md` §6, §11) is that this
swap is exactly this small.

**Log scrubbing note for `activity_logger.py`:** once `JoinCommand`
gains a `password` field (§8), `ActivityLogger._write()`
(`server/logging_/activity_logger.py`) must not log it verbatim — it
currently logs `trace_id`/`connection_id`/`type`/etc. via `getattr`, not
the full record body, so as written today it's already safe; this is
called out so nobody "improves" the logger later to dump full command
payloads without noticing that would leak plaintext passwords into logs.

## 12. Rollout phases & regression gate

Same discipline as `docs/SERVER_PLAN.md` §14: every phase ends with
`python -m pytest` green (existing suite unchanged) and `import-linter`
reporting zero violations.

| Phase | Adds | Proven by |
|---|---|---|
| A | `persistence/models.py`, `db.py`, `schema.sql`, extended `UserRepository`/new `GameRepository` Protocols, `InMemoryUserRepository`/`InMemoryGameRepository` rewrites | `apply_schema()` idempotency; `:memory:` connections are independent; Protocol shape compiles against both Sqlite and InMemory impls |
| B | `sqlite_user_repository.py`, `sqlite_game_repository.py`, `elo.py`, password hashing | Full `:memory:`-backed repository test suite (§10); ELO pure-function tests |
| C | `results/game_result_recorder.py`, `main.py` wiring | `GameResultRecorder` test suite (§10) using real `GameSession` + fake repositories |
| D | `JoinCommand.password`, `ErrorCode.INVALID_CREDENTIALS`, `JoinHandler` rewrite, `ServerConfig.database_path` | Codec round-trip for the new field/error code; `JoinHandler` auth-success/auth-failure tests; one real end-to-end test (mirroring `tests/server/test_e2e.py`) driving create-account → disconnect → re-join with correct/incorrect password over a real `websockets` client against a `:memory:`-backed server |

## 13. Known limitations accepted for now

Same "named, not hidden" discipline as `docs/SERVER_PLAN.md` §16:

- **PBKDF2, not Argon2/bcrypt** (§7) — a deliberate dependency-count
  trade-off for a local/classroom deployment, to revisit together with
  the transport's cleartext-`ws://` limitation if this ever leaves that
  context.
- **No migration framework** (§6) — fine for two tables and one
  deployment; the trigger to add one is a real breaking schema change,
  not a speculative future one.
- **No connection pool / thread offloading for SQLite calls** (§6) — a
  deliberate simplicity choice given the single-threaded `asyncio` model
  and sub-millisecond local SQLite latency; `asyncio.to_thread(...)` is
  the documented, localized escape hatch if that assumption stops
  holding.
- **No mid-game persistence/resume** (§1) — a server restart still loses
  in-progress games; this plan only persists accounts and finished-game
  history, matching what was actually asked for.
- **Full login UX (client-side error presentation, whether "wrong
  password" and "no such user" look different to a human) is
  undesigned** — §8 fixes the wire contract (one `INVALID_CREDENTIALS`
  code, indistinguishable by design at the protocol level, for the same
  security reason many real login systems don't distinguish them) but
  the `ui/net/` client-side plan owns how that's presented.
