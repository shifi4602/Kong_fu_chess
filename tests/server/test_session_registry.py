from kungfu_chess.engine import GameSnapshot
from kungfu_chess.model import Board, Color

from server.bus.event_bus import EventBus
from server.config import ServerConfig
from server.session.game_session import GameSession
from server.session.manual_clock import ManualClock
from server.session.session_registry import SessionRegistry


class FakeEngine:
    def __init__(self) -> None:
        self.winner = None

    def tick(self) -> None:
        pass

    def get_snapshot(self) -> GameSnapshot:
        return GameSnapshot(board=Board(), motions=[], jumps=[], winner=self.winner, current_time=0.0)

    def request_move(self, request) -> bool:
        return True

    def request_jump(self, position) -> bool:
        return True


def _make_registry_and_session(ttl_ms=100):
    config = ServerConfig(max_step_ms=10_000, session_ttl_after_game_over_ms=ttl_ms)
    registry = SessionRegistry(config)
    engine = FakeEngine()
    session = GameSession(
        session_id="s1",
        engine=engine,
        clock=ManualClock(),
        players={},
        config=config,
        bus=EventBus(),
        now_ms=0,
    )
    registry.add(session)
    return registry, engine, session


def test_unfinished_session_is_never_reaped():
    registry, engine, session = _make_registry_and_session()
    registry.tick_all(10)
    registry.tick_all(1_000_000)
    assert len(registry) == 1
    assert registry.get("s1") is session


def test_finished_session_is_reaped_only_after_ttl_of_engine_time():
    registry, engine, session = _make_registry_and_session(ttl_ms=100)

    registry.tick_all(20)
    engine.winner = Color.WHITE
    registry.tick_all(20)  # winner first observed here -> finished_at_ms = 20

    assert len(registry) == 1  # not reaped yet, grace period not elapsed

    registry.tick_all(90)  # ms_since_finished = 70 < 100
    assert len(registry) == 1

    registry.tick_all(119)  # ms_since_finished = 99 < 100
    assert len(registry) == 1

    registry.tick_all(121)  # ms_since_finished = 101 >= 100
    assert len(registry) == 0
    assert registry.get("s1") is None


def test_multiple_sessions_tick_independently_and_reap_independently():
    config = ServerConfig(max_step_ms=10_000, session_ttl_after_game_over_ms=50)
    registry = SessionRegistry(config)
    engine_a = FakeEngine()
    engine_b = FakeEngine()
    session_a = GameSession("a", engine_a, ManualClock(), {}, config, EventBus(), now_ms=0)
    session_b = GameSession("b", engine_b, ManualClock(), {}, config, EventBus(), now_ms=0)
    registry.add(session_a)
    registry.add(session_b)

    engine_a.winner = Color.WHITE
    registry.tick_all(10)  # a finishes at engine_ms=10, b still playing

    registry.tick_all(70)  # a: ms_since_finished = 60 >= 50 -> reaped; b unaffected
    assert registry.get("a") is None
    assert registry.get("b") is session_b
