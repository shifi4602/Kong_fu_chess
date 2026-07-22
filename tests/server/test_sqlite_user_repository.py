import pytest

from server.persistence import db
from server.persistence.sqlite_user_repository import SqliteUserRepository
from server.persistence.user_repository import InvalidCredentialsError, UsernameTakenError


def _repo():
    return SqliteUserRepository(db.connect(":memory:"))


def test_create_account_then_get_round_trips():
    repo = _repo()
    account = repo.create_account("alice", "pw1")
    assert account.username == "alice"
    assert account.elo_rating == 1200
    assert account.created_at_utc
    assert repo.get("alice") == account


def test_get_returns_none_for_unknown_username():
    repo = _repo()
    assert repo.get("nobody") is None


def test_duplicate_create_account_raises():
    repo = _repo()
    repo.create_account("alice", "pw1")
    with pytest.raises(UsernameTakenError):
        repo.create_account("alice", "pw2")


def test_authenticate_with_correct_password_returns_account():
    repo = _repo()
    repo.create_account("alice", "pw1")
    account = repo.authenticate("alice", "pw1")
    assert account.username == "alice"


def test_authenticate_with_wrong_password_raises_invalid_credentials():
    repo = _repo()
    repo.create_account("alice", "pw1")
    with pytest.raises(InvalidCredentialsError):
        repo.authenticate("alice", "wrong")


def test_authenticate_nonexistent_user_raises_the_same_error_as_wrong_password():
    repo = _repo()
    with pytest.raises(InvalidCredentialsError):
        repo.authenticate("nobody", "anything")


def test_update_rating_persists_across_a_fresh_get():
    repo = _repo()
    repo.create_account("alice", "pw1")
    repo.update_rating("alice", 1350)
    assert repo.get("alice").elo_rating == 1350


def test_password_is_never_stored_in_the_clear():
    conn = db.connect(":memory:")
    repo = SqliteUserRepository(conn)
    repo.create_account("alice", "hunter2")

    row = conn.execute(
        "SELECT password_hash, password_salt FROM accounts WHERE username = 'alice'"
    ).fetchone()
    assert b"hunter2" not in row["password_hash"]
    assert row["password_hash"] != b"hunter2"
    assert isinstance(row["password_salt"], bytes)
    assert len(row["password_salt"]) == 16


def test_same_password_and_salt_hash_deterministically():
    from server.persistence.sqlite_user_repository import _hash_password

    salt = b"0123456789abcdef"
    assert _hash_password("hunter2", salt) == _hash_password("hunter2", salt)


def test_same_password_different_salt_hashes_differently():
    from server.persistence.sqlite_user_repository import _hash_password

    assert _hash_password("hunter2", b"a" * 16) != _hash_password("hunter2", b"b" * 16)


def test_two_accounts_with_the_same_password_get_different_salts_and_hashes():
    repo = _repo()
    repo.create_account("alice", "hunter2")
    repo.create_account("bob", "hunter2")
    conn = repo._conn
    alice_row = conn.execute("SELECT password_hash, password_salt FROM accounts WHERE username = 'alice'").fetchone()
    bob_row = conn.execute("SELECT password_hash, password_salt FROM accounts WHERE username = 'bob'").fetchone()
    assert alice_row["password_salt"] != bob_row["password_salt"]
    assert alice_row["password_hash"] != bob_row["password_hash"]
