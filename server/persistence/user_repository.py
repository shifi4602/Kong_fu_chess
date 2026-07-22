from __future__ import annotations

from typing import Dict, Optional, Protocol

from server.persistence.models import Account


class UsernameTakenError(Exception):
    """Raised by create_account() when the username already exists."""


class InvalidCredentialsError(Exception):
    """Raised by authenticate() when the username doesn't exist or the
    password doesn't match — one error, not two, so a client (or an
    attacker) can't distinguish "wrong password" from "no such user" by
    catching a different exception type.
    """


class UserRepository(Protocol):
    def create_account(self, username: str, password: str) -> Account: ...

    def authenticate(self, username: str, password: str) -> Account: ...

    def get(self, username: str) -> Optional[Account]: ...

    def update_rating(self, username: str, new_rating: int) -> None: ...


class InMemoryUserRepository:
    """Zero-I/O double for tests and for anything that doesn't specifically
    want to exercise SQLite — same Protocol shape and the same exceptions
    as `SqliteUserRepository` (§10 of docs/SQLITE_PERSISTENCE_PLAN.md), just
    backed by plain dicts instead of a database.
    """

    def __init__(self) -> None:
        self._accounts: Dict[str, Account] = {}
        self._passwords: Dict[str, str] = {}

    def create_account(self, username: str, password: str) -> Account:
        if username in self._accounts:
            raise UsernameTakenError(username)
        account = Account(username=username, elo_rating=1200, created_at_utc="")
        self._accounts[username] = account
        self._passwords[username] = password
        return account

    def authenticate(self, username: str, password: str) -> Account:
        if username not in self._accounts or self._passwords[username] != password:
            raise InvalidCredentialsError(username)
        return self._accounts[username]

    def get(self, username: str) -> Optional[Account]:
        return self._accounts.get(username)

    def update_rating(self, username: str, new_rating: int) -> None:
        account = self._accounts[username]
        self._accounts[username] = Account(
            username=account.username, elo_rating=new_rating, created_at_utc=account.created_at_utc
        )

    def __contains__(self, username: str) -> bool:
        return username in self._accounts
