import pytest

from gui import ChessSquare


@pytest.mark.parametrize("square,expected_index", [
    ('a1', 0),
    ('h8', 63),
    ('e4', 28),
    ('c6', 42),
])
def test_square_to_index(self, square, expected_index):
    assert ChessSquare.square_to_index(square) == expected_index
