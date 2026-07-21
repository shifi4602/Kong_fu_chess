import pytest

from server.config import ServerConfig


def test_port_zero_is_valid_for_os_assigned_ephemeral_port():
    config = ServerConfig(port=0)
    assert config.port == 0


def test_defaults_are_valid():
    config = ServerConfig()
    assert config.host == "127.0.0.1"
    assert config.port == 8765


@pytest.mark.parametrize(
    "field, value",
    [
        ("port", -1),
        ("port", 70000),
        ("tick_hz", 0.0),
        ("tick_hz", -1.0),
        ("broadcast_hz", 0.0),
        ("max_step_ms", 0),
        ("max_players_per_session", 0),
        ("heartbeat_interval_ms", 0),
        ("session_ttl_after_game_over_ms", 0),
        ("max_commands_per_second", 0.0),
        ("command_burst", 0),
        ("max_frame_bytes", 0),
    ],
)
def test_invalid_scalar_values_raise(field, value):
    with pytest.raises(ValueError):
        ServerConfig(**{field: value})


def test_broadcast_hz_cannot_exceed_tick_hz():
    with pytest.raises(ValueError):
        ServerConfig(tick_hz=5.0, broadcast_hz=10.0)


def test_heartbeat_timeout_must_exceed_interval():
    with pytest.raises(ValueError):
        ServerConfig(heartbeat_interval_ms=1000, heartbeat_timeout_ms=1000)
    with pytest.raises(ValueError):
        ServerConfig(heartbeat_interval_ms=1000, heartbeat_timeout_ms=500)


def test_from_env_reads_overrides():
    env = {
        "SERVER_HOST": "0.0.0.0",
        "SERVER_PORT": "9000",
        "SERVER_TICK_HZ": "30",
        "SERVER_BROADCAST_HZ": "5",
    }
    config = ServerConfig.from_env(env)
    assert config.host == "0.0.0.0"
    assert config.port == 9000
    assert config.tick_hz == 30.0
    assert config.broadcast_hz == 5.0


def test_from_env_defaults_when_missing():
    config = ServerConfig.from_env({})
    assert config == ServerConfig()


def test_from_env_still_validates():
    with pytest.raises(ValueError):
        ServerConfig.from_env({"SERVER_PORT": "70000"})
