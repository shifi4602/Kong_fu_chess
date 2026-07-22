from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from kungfu_chess.model import Color

from server.transport.connection import Connection


class ConnectionState(Enum):
    """Connecting -> Active -> Disconnected(-counting-down) -> Resigned.
    This milestone drives Active -> Disconnected via the heartbeat
    mechanism (§8); the countdown timer and auto-resign transitions on
    top of that are stage 4 (slide 6), not implemented here.
    """

    CONNECTING = "connecting"
    ACTIVE = "active"
    DISCONNECTED = "disconnected"
    RESIGNED = "resigned"


@dataclass
class PlayerSession:
    id: str
    username: str
    connection: Connection
    color: Color
    state: ConnectionState = ConnectionState.CONNECTING
    last_heartbeat_ms: int = 0
    disconnected_at_ms: Optional[int] = None
