from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Account:
    username: str
    elo_rating: int
    created_at_utc: str
