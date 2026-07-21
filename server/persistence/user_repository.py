from __future__ import annotations

from typing import Protocol, Set


class UserRepository(Protocol):
    """No persistence is needed yet (login/passwords are slide 5), but
    modeling it as a Protocol now means `InMemoryUserRepository` (today)
    and a future `SqliteUserRepository` (slide 5) are swappable via DI
    with zero caller changes (§6).
    """

    def register(self, username: str) -> None:
        """Record that `username` has joined this session."""
        ...


class InMemoryUserRepository:
    def __init__(self) -> None:
        self._usernames: Set[str] = set()

    def register(self, username: str) -> None:
        self._usernames.add(username)

    def __contains__(self, username: str) -> bool:
        return username in self._usernames
