from kungfu_chess.model import Color

from server.bus.event_bus import EventBus
from server.config import ServerConfig
from server.matchmaking.lobby import Lobby
from server.matchmaking.strategy import EloWindowStrategy, FirstTwoJoinersStrategy, Waiter
from server.session.session_factory import GameSessionFactory
from server.session.session_registry import SessionRegistry
from server.transport.connection import FakeConnection


def _make_lobby():
    config = ServerConfig()
    bus = EventBus()
    registry = SessionRegistry(config)
    factory = GameSessionFactory(bus=bus, config=config)
    lobby = Lobby(strategy=FirstTwoJoinersStrategy(), factory=factory, registry=registry)
    return lobby, registry


def test_first_joiner_gets_no_pairing_yet():
    lobby, registry = _make_lobby()
    result = lobby.join(FakeConnection("c1"), "alice", trace_id="t1", now_ms=0, rating=1200)
    assert result is None
    assert len(registry) == 0


def test_second_joiner_completes_pairing():
    lobby, registry = _make_lobby()
    lobby.join(FakeConnection("c1"), "alice", trace_id="t1", now_ms=0, rating=1200)
    result = lobby.join(FakeConnection("c2"), "bob", trace_id="t2", now_ms=100, rating=1200)

    assert result is not None
    assert result.white.username == "alice"
    assert result.white.color == Color.WHITE
    assert result.white_trace_id == "t1"
    assert result.black.username == "bob"
    assert result.black.color == Color.BLACK
    assert result.black_trace_id == "t2"
    assert len(registry) == 1
    assert registry.get(result.session.session_id) is result.session


def test_third_and_fourth_joiners_pair_into_a_second_session():
    lobby, registry = _make_lobby()
    lobby.join(FakeConnection("c1"), "alice", trace_id="t1", now_ms=0, rating=1200)
    first_pair = lobby.join(FakeConnection("c2"), "bob", trace_id="t2", now_ms=0, rating=1200)

    assert lobby.join(FakeConnection("c3"), "carol", trace_id="t3", now_ms=0, rating=1200) is None
    second_pair = lobby.join(FakeConnection("c4"), "dave", trace_id="t4", now_ms=0, rating=1200)

    assert second_pair is not None
    assert second_pair.session.session_id != first_pair.session.session_id
    assert len(registry) == 2


def test_first_two_joiners_strategy_returns_none_with_fewer_than_two():
    strategy = FirstTwoJoinersStrategy()
    waiter = Waiter(connection=FakeConnection("c1"), username="alice", trace_id="t1")
    assert strategy.try_match([], now_ms=0) is None
    assert strategy.try_match([waiter], now_ms=0) is None


def test_first_two_joiners_strategy_matches_first_two_in_order():
    strategy = FirstTwoJoinersStrategy()
    w1 = Waiter(connection=FakeConnection("c1"), username="alice", trace_id="t1")
    w2 = Waiter(connection=FakeConnection("c2"), username="bob", trace_id="t2")
    w3 = Waiter(connection=FakeConnection("c3"), username="carol", trace_id="t3")
    assert strategy.try_match([w1, w2, w3], now_ms=0) == (w1, w2)


def _waiter(conn_id: str, username: str, rating: int, joined_at_ms: int = 0) -> Waiter:
    return Waiter(
        connection=FakeConnection(conn_id),
        username=username,
        trace_id=f"t-{conn_id}",
        rating=rating,
        joined_at_ms=joined_at_ms,
    )


def test_elo_window_returns_none_with_fewer_than_two_waiters():
    strategy = EloWindowStrategy()
    assert strategy.try_match([], now_ms=0) is None
    assert strategy.try_match([_waiter("c1", "alice", 1200)], now_ms=0) is None


def test_elo_window_pairs_the_closest_ratings_not_arrival_order():
    strategy = EloWindowStrategy(base_window=50, window_growth_per_second=0, max_wait_ms=60_000)
    far = _waiter("c1", "alice", 1000)
    near_a = _waiter("c2", "bob", 1210)
    near_b = _waiter("c3", "carol", 1200)

    match = strategy.try_match([far, near_a, near_b], now_ms=0)
    assert match == (near_b, near_a)  # 10-point gap beats the 200+ gap to `far`


def test_elo_window_rejects_a_gap_wider_than_the_base_window():
    strategy = EloWindowStrategy(base_window=50, window_growth_per_second=0, max_wait_ms=60_000)
    a = _waiter("c1", "alice", 1000)
    b = _waiter("c2", "bob", 1100)

    assert strategy.try_match([a, b], now_ms=0) is None


def test_elo_window_widens_over_time_until_a_wide_gap_becomes_eligible():
    strategy = EloWindowStrategy(base_window=50, window_growth_per_second=100, max_wait_ms=60_000)
    a = _waiter("c1", "alice", 1000, joined_at_ms=0)
    b = _waiter("c2", "bob", 1100, joined_at_ms=0)

    assert strategy.try_match([a, b], now_ms=100) is None  # window still 50 + 100*0.1 = 60
    assert strategy.try_match([a, b], now_ms=1000) == (a, b)  # window now 50 + 100*1.0 = 150 >= 100


def test_elo_window_max_wait_forces_a_match_regardless_of_rating_gap():
    strategy = EloWindowStrategy(base_window=10, window_growth_per_second=0, max_wait_ms=5_000)
    a = _waiter("c1", "alice", 800, joined_at_ms=0)
    b = _waiter("c2", "bob", 2400, joined_at_ms=0)

    assert strategy.try_match([a, b], now_ms=4_999) is None
    assert strategy.try_match([a, b], now_ms=5_000) == (a, b)


def test_elo_window_earlier_joiner_is_first_in_the_returned_pair():
    strategy = EloWindowStrategy(base_window=100, window_growth_per_second=0, max_wait_ms=60_000)
    earlier = _waiter("c1", "alice", 1200, joined_at_ms=0)
    later = _waiter("c2", "bob", 1210, joined_at_ms=50)

    assert strategy.try_match([earlier, later], now_ms=100) == (earlier, later)


def _make_elo_lobby(base_window=100, window_growth_per_second=40.0, max_wait_ms=60_000):
    config = ServerConfig()
    bus = EventBus()
    registry = SessionRegistry(config)
    factory = GameSessionFactory(bus=bus, config=config)
    strategy = EloWindowStrategy(base_window, window_growth_per_second, max_wait_ms)
    lobby = Lobby(strategy=strategy, factory=factory, registry=registry)
    return lobby, registry


def test_lobby_with_many_waiters_pairs_by_rating_not_join_order():
    # A queue with three waiters: alice (1200) joins first, then a very
    # different-rated dave (2000), then bob (1210) — close to alice. The
    # rating-aware strategy should pair alice with bob, leaving dave still
    # waiting, even though dave joined before bob.
    lobby, registry = _make_elo_lobby(base_window=50, window_growth_per_second=0)
    lobby.join(FakeConnection("c-alice"), "alice", trace_id="t1", now_ms=0, rating=1200)
    assert lobby.join(FakeConnection("c-dave"), "dave", trace_id="t2", now_ms=0, rating=2000) is None

    result = lobby.join(FakeConnection("c-bob"), "bob", trace_id="t3", now_ms=0, rating=1210)

    assert result is not None
    assert {result.white.username, result.black.username} == {"alice", "bob"}
    assert len(registry) == 1


def test_lobby_eventually_pairs_a_lone_extreme_rating_after_the_window_widens():
    lobby, registry = _make_elo_lobby(base_window=10, window_growth_per_second=0, max_wait_ms=1_000)
    lobby.join(FakeConnection("c1"), "alice", trace_id="t1", now_ms=0, rating=800)

    assert lobby.join(FakeConnection("c2"), "bob", trace_id="t2", now_ms=500, rating=2400) is None

    result = lobby.join(FakeConnection("c3"), "carol", trace_id="t3", now_ms=1_500, rating=1500)
    assert result is not None  # alice's max_wait_ms elapsed -> matched with whoever's closest available


def test_remove_waiter_drops_a_disconnected_queued_connection():
    lobby, registry = _make_lobby()
    lobby.join(FakeConnection("c1"), "alice", trace_id="t1", now_ms=0, rating=1200)

    lobby.remove_waiter("c1")

    result = lobby.join(FakeConnection("c2"), "bob", trace_id="t2", now_ms=0, rating=1200)
    assert result is None  # alice was removed — bob is now the sole (unmatched) waiter
    assert len(registry) == 0


def test_remove_waiter_is_a_no_op_for_an_unknown_connection():
    lobby, registry = _make_lobby()
    lobby.remove_waiter("never-joined")  # must not raise
    assert len(registry) == 0
