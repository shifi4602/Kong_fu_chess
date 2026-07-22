from __future__ import annotations

import hashlib
import hmac
import secrets
import sqlite3
from typing import Optional

from server.persistence.models import Account
from server.persistence.user_repository import InvalidCredentialsError, UsernameTakenError

_PBKDF2_ITERATIONS = 200_000
_SALT_BYTES = 16


def _hash_password(password: str, salt: bytes) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _PBKDF2_ITERATIONS)


class SqliteUserRepository:
    """Takes an already-open `sqlite3.Connection` — doesn't open its own.
    `server/persistence/db.py` is the one place that knows the file path,
    PRAGMAs, and schema bootstrapping; this is pure query/mutation logic
    on top of a connection someone else handed it.

    Only `password_hash` (a PBKDF2 digest) and `password_salt` (random,
    per-account) are ever stored — never the plaintext password.
    """

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def create_account(self, username: str, password: str) -> Account:
        if self.get(username) is not None:
            raise UsernameTakenError(username)
        salt = secrets.token_bytes(_SALT_BYTES)
        password_hash = _hash_password(password, salt)
        with self._conn:
            self._conn.execute(
                "INSERT INTO accounts (username, password_hash, password_salt) VALUES (?, ?, ?)",
                (username, password_hash, salt),
            )
        account = self.get(username)
        assert account is not None
        return account

    def authenticate(self, username: str, password: str) -> Account:
        row = self._conn.execute(
            "SELECT password_hash, password_salt FROM accounts WHERE username = ?", (username,)
        ).fetchone()
        if row is None or not hmac.compare_digest(
            _hash_password(password, row["password_salt"]), row["password_hash"]
        ):
            raise InvalidCredentialsError(username)
        account = self.get(username)
        assert account is not None
        return account

    def get(self, username: str) -> Optional[Account]:
        row = self._conn.execute(
            "SELECT username, elo_rating, created_at_utc FROM accounts WHERE username = ?",
            (username,),
        ).fetchone()
        return None if row is None else Account(**row)

    def update_rating(self, username: str, new_rating: int) -> None:
        with self._conn:
            self._conn.execute(
                "UPDATE accounts SET elo_rating = ? WHERE username = ?", (new_rating, username)
            )
