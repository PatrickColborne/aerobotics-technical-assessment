from pydantic import BaseModel

class Coordinate(BaseModel):
    """
    Represents a geographic coordinate with latitude and longitude.

    Attributes:
        lat (float): Latitude of the coordinate.
        lng (float): Longitude of the coordinate.
    """
    lat: float
    lng: float

class MissingTreesResponse(BaseModel):
    """
    Response schema for missing trees.

    Attributes:
        missing_trees (list[Coordinate]): List of coordinates where trees are missing.
    """
    missing_trees: list[Coordinate]
