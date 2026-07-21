from server.clock import FakeWallClock
from server.handlers.rate_limiter import RateLimiter


def test_burst_allows_up_to_capacity_then_denies():
    clock = FakeWallClock()
    limiter = RateLimiter(max_per_second=10.0, burst=3, clock=clock)

    assert limiter.allow("c1") is True
    assert limiter.allow("c1") is True
    assert limiter.allow("c1") is True
    assert limiter.allow("c1") is False


def test_tokens_refill_over_fake_time():
    clock = FakeWallClock()
    limiter = RateLimiter(max_per_second=10.0, burst=1, clock=clock)

    assert limiter.allow("c1") is True
    assert limiter.allow("c1") is False

    clock.advance(1000)  # 1 second at 10/s refills to full burst
    assert limiter.allow("c1") is True


def test_connections_are_tracked_independently():
    clock = FakeWallClock()
    limiter = RateLimiter(max_per_second=10.0, burst=1, clock=clock)

    assert limiter.allow("c1") is True
    assert limiter.allow("c1") is False
    assert limiter.allow("c2") is True  # independent bucket
