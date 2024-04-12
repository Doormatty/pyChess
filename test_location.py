from utils import Location

import pytest

def test_location():
    location1 = Location('a7')
    location2 = Location('A7')
    assert location1 == location2
    assert location.x == 10
    assert location.y == 20
