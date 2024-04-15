from enum import Enum


class Color(Enum):
    WHITE = 'White'
    BLACK = 'Black'


class Location:
    class LocationException(Exception):
        pass

    @staticmethod
    def _valid_locations(location):
        if len(location) != 2 or not isinstance(location, str):
            raise Location.LocationException(f'Location must be a string of length 2, not {location}')
        return location[0] in "abcdefgh" and location[1] in "12345678"

    def __init__(self, location: str):
        self.location = str(location).lower()
        if not Location._valid_locations(self.location):
            raise Location.LocationException(f"Invalid location: {self.location}")
        self.file = self.location[0]  # A-H
        self.int_file = ord(self.file)
        self.rank = int(self.location[1])  # 1-8

    def __repr__(self):
        return f"{self.location}"

    def __str__(self):
        return f"{self.location}"

    def __getitem__(self, item):
        if not isinstance(item, int):
            raise TypeError("Only integers are allowed")
        if len(str(item)) > 2 or len(str(item)) < 1:
            raise ValueError("Location string does not have length 2")
        return self.location[item]

    def __sub__(self, other: 'Location | tuple | str') -> 'Location | tuple':
        if isinstance(other, Location):
            return self.int_file - other.int_file, self.rank - other.rank
        if isinstance(other, tuple):
            return Location(chr(self.int_file - other[0]) + str(self.rank - other[1]))
        if isinstance(other, str):
            other = Location(other)
            return self.int_file - other.int_file, self.rank - other.rank
        raise TypeError

    def __add__(self, other: tuple[int, int]) -> 'Location':
        return Location(chr(self.int_file + other[0]) + str(self.rank + other[1]))

    def __eq__(self, other: 'Location | str | None') -> bool:
        if isinstance(other, Location):
            return self.file == other.file and self.rank == other.rank
        if isinstance(other, str):
            return self.location == other
        if other is None or not other:
            return False
        raise NotImplementedError

    def __hash__(self):
        return hash((self.file, self.rank))
