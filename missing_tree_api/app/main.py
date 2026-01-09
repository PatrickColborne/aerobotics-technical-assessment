from fastapi import FastAPI
from pydantic import BaseModel
from aerobotics.client import AeroboticsClient
from aerobotics.models import TreeSurvey, Page

# requests or httpx? Should I make this all asynchronous for speed? It probably doesn't matter for this demo.

app = FastAPI()

aerobotics_client = AeroboticsClient(
    base_url="https://api.aerobotics.com",
    api_key="4c80d904cae3d86b472fd636ef9d78a36faea104c61c7018a3604285d552d5e4"
)

# Represents a coordinate with latitude and longitude
class Coordinate(BaseModel):
    lat: float
    lng: float

# The response model for missing trees
class MissingTreesResponse(BaseModel):
        missing_trees: list[Coordinate]

@app.get("/orchards/{id}/missing-trees", response_model=MissingTreesResponse)
async def get_missing_trees(id: int):

    surveys: Page[TreeSurvey] = await aerobotics_client.get_tree_surveys(id)

    missing_trees = [
        Coordinate(lat=tree_survey.lat, lng=tree_survey.lng)
        for tree_survey in surveys.results
    ]

    return MissingTreesResponse(missing_trees=missing_trees)



# Thinking about how to find missing trees here.

# For the tree survey, we need to find the distance between each tree and its nearest neighbor and probably on 2 axis (row and column).
# Once we find the median distance between trees, we can set a threshold (e.g., 1.5x median distance) to identify missing trees.
# For each tree, we can check if there is another tree within the threshold distance in both axes.
# If not, we can consider that position as a missing tree.

# We could use a KD Tree but the data is already in a grid format so we don't need to know the row and column indices of each tree to find missing trees.
