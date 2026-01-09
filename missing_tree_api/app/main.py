from fastapi import FastAPI
from pydantic import BaseModel

# requests or httpx? Should I make this all asynchronous for speed? It probably doesn't matter for this demo.

app = FastAPI()

# Represents a coordinate with latitude and longitude
class Coordinate(BaseModel):
    lat: float
    lng: float

# The response model for missing trees
class MissingTreesResponse(BaseModel):
        missing_trees: list[Coordinate]

@app.get("/orchards/{id}/missing-trees", response_model=MissingTreesResponse)
async def get_missing_trees(id: int):
    # For demonstration, return a static list of missing tree coordinates
    missing_trees = [
        Coordinate(lat=37.7749, lng=-122.4194),
        Coordinate(lat=34.0522, lng=-118.2437),
    ]

    return MissingTreesResponse(missing_trees=missing_trees)