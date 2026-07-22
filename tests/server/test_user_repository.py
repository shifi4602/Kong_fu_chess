import pytest

from server.persistence.user_repository import (
    InMemoryUserRepository,
    InvalidCredentialsError,
    UsernameTakenError,
)


def test_create_account_then_get_round_trips():
    repo = InMemoryUserRepository()
    assert "alice" not in repo
    account = repo.create_account("alice", "pw1")
    assert account.username == "alice"
    assert account.elo_rating == 1200
    assert "alice" in repo
    assert repo.get("alice") == account


def test_get_returns_none_for_unknown_username():
    repo = InMemoryUserRepository()
    assert repo.get("nobody") is None


def test_duplicate_create_account_raises():
    repo = InMemoryUserRepository()
    repo.create_account("alice", "pw1")
    with pytest.raises(UsernameTakenError):
        repo.create_account("alice", "pw2")


def test_authenticate_with_correct_password_returns_account():
    repo = InMemoryUserRepository()
    repo.create_account("alice", "pw1")
    account = repo.authenticate("alice", "pw1")
    assert account.username == "alice"


def test_authenticate_with_wrong_password_raises_invalid_credentials():
    repo = InMemoryUserRepository()
    repo.create_account("alice", "pw1")
    with pytest.raises(InvalidCredentialsError):
        repo.authenticate("alice", "wrong")


def test_authenticate_nonexistent_user_raises_the_same_error_as_wrong_password():
    repo = InMemoryUserRepository()
    with pytest.raises(InvalidCredentialsError):
        repo.authenticate("nobody", "anything")


def test_update_rating_persists_across_a_fresh_get():
    repo = InMemoryUserRepository()
    repo.create_account("alice", "pw1")
    repo.update_rating("alice", 1350)
    assert repo.get("alice").elo_rating == 1350
