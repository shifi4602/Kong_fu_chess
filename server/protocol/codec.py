from __future__ import annotations

import dataclasses
import json
from enum import Enum
from typing import Any, Dict, Type, Union, get_args, get_origin, get_type_hints

from .commands import HeartbeatCommand, JoinCommand, JumpCommand, MoveCommand
from .events import (
    ErrorEvent,
    GameOverEvent,
    HeartbeatEvent,
    MoveRejectedEvent,
    PlayerJoinedEvent,
    StateEvent,
    WelcomeEvent,
)

# `type` discriminator -> dataclass. This is the only place a wire `type`
# string is mapped to a record class — the Factory §6 refers to. NoOpEvent
# is deliberately absent: it never crosses the wire (see protocol/events.py).
_COMMAND_TYPES: Dict[str, Type] = {
    "join": JoinCommand,
    "move": MoveCommand,
    "jump": JumpCommand,
    "heartbeat": HeartbeatCommand,
}

_EVENT_TYPES: Dict[str, Type] = {
    "welcome": WelcomeEvent,
    "player_joined": PlayerJoinedEvent,
    "state": StateEvent,
    # Distinct from the "heartbeat" command discriminator below — every
    # wire `type` string must be globally unique since a raw frame carries
    # no separate command-vs-event tag, only `type` (§5).
    "heartbeat_ack": HeartbeatEvent,
    "move_rejected": MoveRejectedEvent,
    "game_over": GameOverEvent,
    "error": ErrorEvent,
}

_ALL_TYPES: Dict[str, Type] = {**_COMMAND_TYPES, **_EVENT_TYPES}
_TYPE_NAMES: Dict[Type, str] = {cls: name for name, cls in _ALL_TYPES.items()}


class UnknownCommandError(Exception):
    """Decoded JSON has a `type` field this codec doesn't recognize."""

    def __init__(self, type_name: Any) -> None:
        super().__init__(f"unknown command type: {type_name!r}")
        self.type_name = type_name


class MalformedMessageError(Exception):
    """Decoded JSON's `type` was recognized but its fields didn't decode."""


def encode(record: Any) -> str:
    type_name = _TYPE_NAMES.get(type(record))
    if type_name is None:
        raise TypeError(f"{type(record).__name__} is not a registered wire record")
    payload = _encode_value(record)
    payload["type"] = type_name
    return json.dumps(payload)


def type_name_for(record: Any) -> str:
    """Public accessor for a record's wire `type` discriminator, without
    encoding it — used by `logging_/activity_logger.py` (§4) to log a
    record's type alongside `trace_id`/`connection_id`.
    """
    type_name = _TYPE_NAMES.get(type(record))
    if type_name is None:
        raise TypeError(f"{type(record).__name__} is not a registered wire record")
    return type_name


def decode(raw: str) -> Any:
    """Decode any registered Command or Event. Total: never returns None,
    never raises a bare exception — always UnknownCommandError or
    MalformedMessageError, per §5.
    """
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise MalformedMessageError(f"invalid JSON: {exc}") from exc

    if not isinstance(payload, dict):
        raise MalformedMessageError("top-level JSON value must be an object")
    if "type" not in payload:
        raise MalformedMessageError("missing 'type' field")

    type_name = payload["type"]
    cls = _ALL_TYPES.get(type_name)
    if cls is None:
        raise UnknownCommandError(type_name)

    fields = {k: v for k, v in payload.items() if k != "type"}
    try:
        return _decode_dataclass(cls, fields)
    except (KeyError, TypeError, ValueError) as exc:
        raise MalformedMessageError(str(exc)) from exc


def decode_command(raw: str) -> Any:
    """Like decode(), but restricted to the command registry — used by
    transport/ws_server.py, which should never accept an Event from a
    client."""
    return _decode_restricted(raw, _COMMAND_TYPES)


def decode_event(raw: str) -> Any:
    """Like decode(), but restricted to the event registry — for a future
    client-side decoder."""
    return _decode_restricted(raw, _EVENT_TYPES)


def _decode_restricted(raw: str, registry: Dict[str, Type]) -> Any:
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise MalformedMessageError(f"invalid JSON: {exc}") from exc

    if not isinstance(payload, dict):
        raise MalformedMessageError("top-level JSON value must be an object")
    if "type" not in payload:
        raise MalformedMessageError("missing 'type' field")

    type_name = payload["type"]
    cls = registry.get(type_name)
    if cls is None:
        raise UnknownCommandError(type_name)

    fields = {k: v for k, v in payload.items() if k != "type"}
    try:
        return _decode_dataclass(cls, fields)
    except (KeyError, TypeError, ValueError) as exc:
        raise MalformedMessageError(str(exc)) from exc


def _encode_value(value: Any) -> Any:
    if dataclasses.is_dataclass(value):
        return {f.name: _encode_value(getattr(value, f.name)) for f in dataclasses.fields(value)}
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, (tuple, list)):
        return [_encode_value(v) for v in value]
    return value


def _decode_dataclass(cls: Type, fields_dict: Dict[str, Any]) -> Any:
    hints = get_type_hints(cls)
    kwargs = {}
    for f in dataclasses.fields(cls):
        if f.name not in fields_dict:
            raise KeyError(f"missing field '{f.name}' for {cls.__name__}")
        kwargs[f.name] = _decode_value(hints[f.name], fields_dict[f.name])
    return cls(**kwargs)


def _decode_value(type_hint: Any, raw: Any) -> Any:
    origin = get_origin(type_hint)

    if origin is Union:
        args = [a for a in get_args(type_hint) if a is not type(None)]
        if raw is None:
            return None
        return _decode_value(args[0], raw)

    if origin is tuple:
        if not isinstance(raw, list):
            raise TypeError(f"expected a list, got {type(raw).__name__}")
        (elem_type, *_rest) = get_args(type_hint)
        return tuple(_decode_value(elem_type, v) for v in raw)

    if dataclasses.is_dataclass(type_hint):
        if not isinstance(raw, dict):
            raise TypeError(f"expected an object for {type_hint.__name__}, got {type(raw).__name__}")
        return _decode_dataclass(type_hint, raw)

    if isinstance(type_hint, type) and issubclass(type_hint, Enum):
        try:
            return type_hint(raw)
        except ValueError as exc:
            raise ValueError(f"invalid value {raw!r} for {type_hint.__name__}") from exc

    if type_hint is float:
        if not isinstance(raw, (int, float)) or isinstance(raw, bool):
            raise TypeError(f"expected a number, got {type(raw).__name__}")
        return float(raw)

    if type_hint is int:
        if not isinstance(raw, int) or isinstance(raw, bool):
            raise TypeError(f"expected an int, got {type(raw).__name__}")
        return raw

    if type_hint is str:
        if not isinstance(raw, str):
            raise TypeError(f"expected a str, got {type(raw).__name__}")
        return raw

    if type_hint is bool:
        if not isinstance(raw, bool):
            raise TypeError(f"expected a bool, got {type(raw).__name__}")
        return raw

    return raw
