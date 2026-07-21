from server.persistence.user_repository import InMemoryUserRepository


def test_register_and_contains():
    repo = InMemoryUserRepository()
    assert "alice" not in repo
    repo.register("alice")
    assert "alice" in repo


def test_register_is_idempotent():
    repo = InMemoryUserRepository()
    repo.register("alice")
    repo.register("alice")
    assert "alice" in repo
