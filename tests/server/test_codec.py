import json

import pytest

from kungfu_chess.model import Color, PieceKind, PieceState, Position
from server.protocol import codec
from server.protocol.commands import HeartbeatCommand, JoinCommand, JumpCommand, MoveCommand
from server.protocol.errors import ErrorCode
from server.protocol.events import (
    ErrorEvent,
    GameOverEvent,
    HeartbeatEvent,
    MoveRejectedEvent,
    PlayerJoinedEvent,
    StateEvent,
    WelcomeEvent,
)
from server.protocol.state_records import JumpRecord, MotionRecord, PieceRecord


def _roundtrip(record):
    raw = codec.encode(record)
    decoded = codec.decode(raw)
    assert decoded == record
    return raw


def test_join_command_roundtrip():
    _roundtrip(JoinCommand(trace_id="t1", username="alice"))


def test_move_command_roundtrip():
    cmd = MoveCommand(trace_id="t2", src=Position(1, 2), dst=Position(3, 4))
    raw = _roundtrip(cmd)
    payload = json.loads(raw)
    assert payload["type"] == "move"
    assert payload["src"] == {"row": 1, "col": 2}


def test_jump_command_roundtrip():
    _roundtrip(JumpCommand(trace_id="t3", position=Position(0, 0)))


def test_heartbeat_command_roundtrip():
    _roundtrip(HeartbeatCommand(trace_id="t4", client_send_ms=12345))


def test_welcome_event_roundtrip():
    _roundtrip(WelcomeEvent(trace_id="t5", connection_id="c1", color=Color.WHITE))


def test_player_joined_event_roundtrip():
    _roundtrip(PlayerJoinedEvent(trace_id="t6", color=Color.BLACK))


def test_state_event_roundtrip_with_nested_records():
    piece = PieceRecord(
        id="p1", color=Color.WHITE, kind=PieceKind.PAWN, cell=Position(1, 1), state=PieceState.IDLE
    )
    motion = MotionRecord(
        piece_id="p2",
        src=Position(1, 1),
        dst=Position(3, 1),
        path=(Position(1, 1), Position(2, 1), Position(3, 1)),
        start_time=1.5,
        duration=2.0,
    )
    jump = JumpRecord(piece_id="p3", cell=Position(4, 4), start_time=0.5, duration=1.0)
    event = StateEvent(
        trace_id="t7",
        pieces=(piece,),
        motions=(motion,),
        jumps=(jump,),
        current_time=3.25,
        winner=None,
    )
    _roundtrip(event)


def test_state_event_roundtrip_with_winner_set():
    event = StateEvent(
        trace_id="t8", pieces=(), motions=(), jumps=(), current_time=10.0, winner=Color.BLACK
    )
    _roundtrip(event)


def test_heartbeat_event_roundtrip():
    _roundtrip(
        HeartbeatEvent(trace_id="t9", connection_id="c2", client_send_ms=100, server_time_ms=105)
    )


def test_move_rejected_event_roundtrip():
    _roundtrip(
        MoveRejectedEvent(trace_id="t10", connection_id="c3", reason=ErrorCode.NOT_YOUR_PIECE)
    )


def test_game_over_event_roundtrip():
    _roundtrip(GameOverEvent(trace_id="t11", winner=Color.WHITE))


def test_error_event_roundtrip():
    _roundtrip(ErrorEvent(trace_id="t12", connection_id="c4", reason=ErrorCode.MALFORMED_MESSAGE))


@pytest.mark.parametrize("code", list(ErrorCode))
def test_every_error_code_roundtrips(code):
    _roundtrip(ErrorEvent(trace_id="t13", connection_id="c5", reason=code))


def test_unknown_type_raises_typed_error_not_none():
    raw = json.dumps({"type": "resign", "trace_id": "t14"})
    with pytest.raises(codec.UnknownCommandError) as exc_info:
        codec.decode(raw)
    assert exc_info.value.type_name == "resign"


def test_missing_type_field_raises_malformed():
    raw = json.dumps({"trace_id": "t15"})
    with pytest.raises(codec.MalformedMessageError):
        codec.decode(raw)


def test_invalid_json_raises_malformed():
    with pytest.raises(codec.MalformedMessageError):
        codec.decode("not json at all")


def test_missing_field_raises_malformed():
    raw = json.dumps({"type": "join", "trace_id": "t16"})  # missing username
    with pytest.raises(codec.MalformedMessageError):
        codec.decode(raw)


def test_wrong_field_type_raises_malformed():
    raw = json.dumps({"type": "heartbeat", "trace_id": "t17", "client_send_ms": "not-an-int"})
    with pytest.raises(codec.MalformedMessageError):
        codec.decode(raw)


def test_invalid_enum_value_raises_malformed():
    raw = json.dumps(
        {"type": "welcome", "trace_id": "t18", "connection_id": "c6", "color": "purple"}
    )
    with pytest.raises(codec.MalformedMessageError):
        codec.decode(raw)


def test_decode_command_rejects_event_type():
    raw = codec.encode(GameOverEvent(trace_id="t19", winner=Color.WHITE))
    with pytest.raises(codec.UnknownCommandError):
        codec.decode_command(raw)


def test_decode_event_rejects_command_type():
    raw = codec.encode(JoinCommand(trace_id="t20", username="bob"))
    with pytest.raises(codec.UnknownCommandError):
        codec.decode_event(raw)


def test_encode_rejects_unregistered_type():
    class NotARecord:
        pass

    with pytest.raises(TypeError):
        codec.encode(NotARecord())


def test_command_and_event_discriminators_never_collide():
    command_names = set(codec._COMMAND_TYPES)
    event_names = set(codec._EVENT_TYPES)
    assert command_names.isdisjoint(event_names)
    assert len(codec._TYPE_NAMES) == len(codec._COMMAND_TYPES) + len(codec._EVENT_TYPES)
