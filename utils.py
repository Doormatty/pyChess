from enum import Enum


class Color(Enum):
    WHITE = 'White'
    BLACK = 'Black'


class Location:
    class LocationException(Exception):
        pass

    @staticmethod
    def _valid_locations(location):
        return location[0] in "abcdefgh" and location[1] in "12345678"

    def __init__(self, location):
        self.location = location.lower()
        if not Location._valid_locations(self.location):
            raise Location.LocationException(f"Invalid location: {self.location}")
        self.file = self.location[0]
        self.int_file = ord(self.file)
        self.rank = self.location[1]

    def __repr__(self):
        return f"{self.location}"

    def __str__(self):
        return f"{self.location}"

    def __sub__(self, other: 'Location' | tuple[int, int]) -> 'Location' | tuple[int, int]:
        if isinstance(other, Location):
            return self.int_file - other.int_file, self.rank - other.rank
        if isinstance(other, tuple):
            return Location(chr(self.int_file - other[0]) + str(self.rank - other[1]))

    def _add__(self, other: tuple[int, int]) -> 'Location':
        return Location(chr(self.int_file + other[0]) + str(self.rank + other[1]))

    def __eq__(self, other: 'Location') -> bool:
        if not isinstance(other, Location):
            raise NotImplementedError
        return self.file == other.file and self.rank == other.rank

    def __hash__(self):
        return hash((self.file, self.rank))
