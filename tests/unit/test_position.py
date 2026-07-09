import pytest
from kungfu_chess.model import Position


def test_equality():
    assert Position(1, 2) == Position(1, 2)


def test_inequality_row():
    assert Position(1, 2) != Position(2, 2)


def test_inequality_col():
    assert Position(1, 2) != Position(1, 3)


def test_hashable_as_dict_key():
    d = {Position(0, 0): 'origin', Position(1, 2): 'other'}
    assert d[Position(0, 0)] == 'origin'
    assert d[Position(1, 2)] == 'other'


def test_frozen_row():
    pos = Position(1, 2)
    with pytest.raises(Exception):
        pos.row = 5


def test_frozen_col():
    pos = Position(1, 2)
    with pytest.raises(Exception):
        pos.col = 5
