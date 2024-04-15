import pytest

from utils import Location


class TestLocationInitialization:
    @pytest.mark.parametrize("valid_location", ["a1", "h8", "e4", "b2", "g7"])
    def test_valid_initialization(self, valid_location):
        # No exception should be raised for valid locations
        try:
            location = Location(valid_location)
            assert location.location == valid_location.lower(), "Location should be stored in lowercase"
        except Exception as e:
            pytest.fail(f"Unexpected exception for valid location '{valid_location}': {e}")

    @pytest.mark.parametrize("invalid_location", ["i1", "a9", "z34", "b0", "88", "", "11", "aa"])
    def test_invalid_initialization(self, invalid_location):
        with pytest.raises(Location.LocationException):
            Location(invalid_location)


class TestLocationStringRepresentations:
    @pytest.mark.parametrize("location_str", ["A1", "h8", "E4", "B2", "G7"])
    def test_repr_and_str(self, location_str):
        location = Location(location_str)
        expected_str = location_str.lower()
        assert repr(location) == expected_str, f"repr should return the lowercase location string {expected_str}"
        assert str(location) == expected_str, f"str should return the lowercase location string {expected_str}"


class TestLocationArithmeticOperations:
    def test_subtraction_with_location(self):
        loc_a = Location("e2")
        loc_b = Location("d2")
        assert loc_a - loc_b == (1, 0), "Subtraction should return the correct difference in file and rank"
        assert loc_b - loc_a == (-1, 0), "Subtraction should return the correct difference in file and rank"

    def test_subtraction_with_invalid_type(self):
        loc = Location("e2")
        with pytest.raises(TypeError):
            _ = loc - "invalid type"

    def test_addition_with_tuple(self):
        loc = Location("e2")
        result = loc + (1, 1)
        assert isinstance(result, Location), "Addition should return a new Location instance"
        assert result.location == "f3", "Addition should correctly update the file and rank"

    def test_addition_with_invalid_type(self):
        loc = Location("e2")
        with pytest.raises(TypeError):
            _ = loc + "invalid type"


class TestLocationEqualityAndHashing:
    def test_equality_with_same_location(self):
        loc_a = Location("a1")
        loc_b = Location("a1")
        assert loc_a == loc_b, "Two Location instances with the same state should be considered equal"

    def test_equality_with_different_location(self):
        loc_a = Location("a1")
        loc_b = Location("a2")
        assert loc_a != loc_b, "Two Location instances with different states should not be considered equal"

    def test_hash_equality(self):
        loc_a = Location("a1")
        loc_b = Location("a1")
        assert hash(loc_a) == hash(loc_b), "Two Location instances with the same state should have the same hash value"
        loc_set = {loc_a, loc_b}
        assert len(loc_set) == 1, "A set should eliminate duplicate Location instances based on their state"
