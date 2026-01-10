import math
import statistics
from typing import List

from pydantic import BaseModel

EARTH_RADIUS_M = 6371000  # meters

class Vector(BaseModel):
    dx: float  # east/west in meters
    dy: float  # north/south in meters

    @property
    def magnitude(self) -> float:
        """Euclidean distance in meters."""
        return (self.dx**2 + self.dy**2) ** 0.5

    @staticmethod
    def median_vector(vectors: List["Vector"]) -> "Vector":
        """
        Computes the median vector from a list of Vector objects.
        """
        if not vectors:
            raise ValueError("Vector list cannot be empty")

        dxs = [v.dx for v in vectors]
        dys = [v.dy for v in vectors]

        median_dx = statistics.median(dxs)
        median_dy = statistics.median(dys)

        return Vector(dx=median_dx, dy=median_dy)

class Coordinate(BaseModel):
    lat: float
    lng: float

    def vector_to(self, other: "Coordinate") -> Vector:
        """
        Returns a Vector (dx, dy in meters) from this coordinate to another.
        dx = east, dy = north
        """
        dlat = math.radians(other.lat - self.lat)
        dlng = math.radians(other.lng - self.lng)
        lat_rad = math.radians(self.lat)

        dy = dlat * EARTH_RADIUS_M
        dx = dlng * EARTH_RADIUS_M * math.cos(lat_rad)

        return Vector(dx=dx, dy=dy)

    def move_by_vector(self, vector: Vector) -> "Coordinate":
        """
        Returns a new Coordinate by applying a Vector (dx, dy in meters)
        to this coordinate.
        """
        new_lat = self.lat + (vector.dy / EARTH_RADIUS_M) * (180 / math.pi)
        new_lng = self.lng + (vector.dx / (EARTH_RADIUS_M * math.cos(math.radians(self.lat)))) * (180 / math.pi)
        return Coordinate(lat=new_lat, lng=new_lng)
