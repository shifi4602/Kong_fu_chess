from enum import Enum


class ErrorCode(Enum):
    NOT_YOUR_PIECE = "not_your_piece"
    ILLEGAL_MOVE = "illegal_move"
    SESSION_FULL = "session_full"
    UNKNOWN_COMMAND = "unknown_command"
    MALFORMED_MESSAGE = "malformed_message"
    RATE_LIMITED = "rate_limited"
