from kungfu_chess.engine import GameSnapshot
from kungfu_chess.model import Board, Color, Position

from server.bus.event_bus import EventBus
from server.bus.topics import OUTBOUND
from server.config import ServerConfig
from server.protocol.commands import MoveCommand
from server.protocol.errors import ErrorCode
from server.protocol.events import GameOverEvent, MoveRejectedEvent, StateEvent
from server.session.game_session import GameSession
from server.session.manual_clock import ManualClock
from server.session.player_session import ConnectionState, PlayerSession
from server.session.session_factory import GameSessionFactory
from server.transport.connection import FakeConnection


class FakeEngine:
    """Duck-typed test double for `kungfu_chess.engine.GameEngine` — only
    the four methods `GameSession` actually calls. Used for the
    game-over/reaping tests, where real board content is irrelevant.
    """

    def __init__(self) -> None:
        self.winner = None
        self.tick_count = 0

    def tick(self) -> None:
        self.tick_count += 1

    def get_snapshot(self) -> GameSnapshot:
        return GameSnapshot(board=Board(), motions=[], jumps=[], winner=self.winner, current_time=0.0)

    def request_move(self, request) -> bool:
        return True

    def request_jump(self, position) -> bool:
        return True


def _bus_and_sink(topic=OUTBOUND):
    bus = EventBus()
    received = []
    bus.subscribe(topic, lambda message: received.append(message.event))
    return bus, received


def _make_session(config=None, now_ms=0):
    if config is None:
        config = ServerConfig(max_step_ms=10_000, heartbeat_interval_ms=10, heartbeat_timeout_ms=50)
    bus, received = _bus_and_sink()
    factory = GameSessionFactory(bus=bus, config=config)
    white_conn = FakeConnection("white-conn")
    black_conn = FakeConnection("black-conn")
    session, players = factory.create(
        white_connection=white_conn,
        white_username="alice",
        black_connection=black_conn,
        black_username="bob",
        now_ms=now_ms,
    )
    return session, players, bus, received


def test_two_sessions_advance_independently():
    config = ServerConfig(max_step_ms=10_000)
    session1, _, _, _ = _make_session(config, now_ms=0)
    session2, _, _, _ = _make_session(config, now_ms=0)

    session1.advance(1000)
    session2.advance(2000)

    assert session1.engine_ms == 1000
    assert session2.engine_ms == 2000


def test_unauthorized_move_is_rejected_without_mutating_board():
    session, players, bus, received = _make_session()
    white_id = "white-conn"

    # White tries to move a black pawn at (1, 0).
    session.enqueue(white_id, MoveCommand(trace_id="t1", src=Position(1, 0), dst=Position(2, 0)))
    session.advance(10)

    rejections = [e for e in received if isinstance(e, MoveRejectedEvent)]
    assert len(rejections) == 1
    assert rejections[0].reason == ErrorCode.NOT_YOUR_PIECE
    assert rejections[0].connection_id == white_id
    assert rejections[0].trace_id == "t1"

    piece = session._engine.get_snapshot().board.get(Position(1, 0))
    assert piece is not None
    assert piece.color == Color.BLACK  # untouched


def test_illegal_move_by_owner_is_rejected():
    session, players, bus, received = _make_session()
    white_id = "white-conn"

    # White pawn at (6,0) cannot jump to (3,0) in one move.
    session.enqueue(white_id, MoveCommand(trace_id="t2", src=Position(6, 0), dst=Position(3, 0)))
    session.advance(10)

    rejections = [e for e in received if isinstance(e, MoveRejectedEvent)]
    assert len(rejections) == 1
    assert rejections[0].reason == ErrorCode.ILLEGAL_MOVE


def test_legal_move_by_owner_is_applied_with_no_rejection():
    session, players, bus, received = _make_session()
    white_id = "white-conn"

    session.enqueue(white_id, MoveCommand(trace_id="t3", src=Position(6, 0), dst=Position(4, 0)))
    session.advance(10)

    rejections = [e for e in received if isinstance(e, MoveRejectedEvent)]
    assert rejections == []
    snapshot = session._engine.get_snapshot()
    assert len(snapshot.motions) == 1
    assert snapshot.motions[0].src == Position(6, 0)
    assert snapshot.motions[0].dst == Position(4, 0)


def test_advance_clamps_large_jump_to_max_step_ms():
    config = ServerConfig(max_step_ms=250)
    session, _, _, _ = _make_session(config, now_ms=0)

    session.advance(100_000)

    assert session.engine_ms == 250


def test_commands_drain_before_clock_advances():
    # A small max_step_ms clamp keeps the motion (duration=2.0s for a
    # two-square pawn move) unresolved after this tick, so we can inspect
    # its start_time before it's cleared from active_motions().
    config = ServerConfig(max_step_ms=10)
    session, _, _, _ = _make_session(config, now_ms=0)
    white_id = "white-conn"

    session.enqueue(white_id, MoveCommand(trace_id="t4", src=Position(6, 0), dst=Position(4, 0)))
    session.advance(5000)

    snapshot = session._engine.get_snapshot()
    # start_motion reads the clock at call time (§9.3); the drain happens
    # before the clock is advanced this tick, so start_time is the *old*
    # engine clock (0.0s), not the post-advance one (0.01s).
    assert len(snapshot.motions) == 1
    assert snapshot.motions[0].start_time == 0.0
    assert session.engine_ms == 10


def test_broadcast_only_fires_at_configured_cadence():
    config = ServerConfig(broadcast_hz=10.0, tick_hz=50.0, max_step_ms=10_000)  # every 100ms
    session, _, _, received = _make_session(config, now_ms=0)

    session.advance(50)  # not yet due
    assert [e for e in received if isinstance(e, StateEvent)] == []

    session.advance(100)  # due
    assert len([e for e in received if isinstance(e, StateEvent)]) == 1

    session.advance(150)  # not yet due again
    assert len([e for e in received if isinstance(e, StateEvent)]) == 1

    session.advance(200)  # due again
    assert len([e for e in received if isinstance(e, StateEvent)]) == 2


def test_liveness_transition_fires_at_configured_threshold():
    config = ServerConfig(heartbeat_interval_ms=10, heartbeat_timeout_ms=50, max_step_ms=10_000)
    session, players, _, _ = _make_session(config, now_ms=0)
    white = players["white-conn"]
    assert white.state == ConnectionState.ACTIVE

    session.advance(50)  # exactly at threshold: not yet exceeded
    assert white.state == ConnectionState.ACTIVE

    session.advance(51)  # now exceeded
    assert white.state == ConnectionState.DISCONNECTED


def test_liveness_does_not_trip_when_heartbeats_keep_arriving():
    config = ServerConfig(heartbeat_interval_ms=10, heartbeat_timeout_ms=50, max_step_ms=10_000)
    session, players, _, _ = _make_session(config, now_ms=0)
    white = players["white-conn"]

    white.last_heartbeat_ms = 40
    session.advance(60)  # 60 - 40 = 20 < 50

    assert white.state == ConnectionState.ACTIVE


def test_game_over_event_published_exactly_once_and_terminal_flag_set():
    bus, received = _bus_and_sink()
    config = ServerConfig(max_step_ms=10_000)
    engine = FakeEngine()
    session = GameSession(
        session_id="s1",
        engine=engine,
        clock=ManualClock(),
        players={},
        config=config,
        bus=bus,
        now_ms=0,
    )

    session.advance(10)
    assert not session.is_terminal

    engine.winner = Color.WHITE
    session.advance(20)
    assert session.is_terminal
    assert session.ms_since_finished == 0

    session.advance(30)  # winner stays set; must not re-publish
    game_overs = [e for e in received if isinstance(e, GameOverEvent)]
    assert len(game_overs) == 1
    assert game_overs[0].winner == Color.WHITE
