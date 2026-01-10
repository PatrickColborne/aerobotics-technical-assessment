from typing import List

from sklearn.cluster import DBSCAN
from scipy.spatial import KDTree
import numpy as np

from fastapi import FastAPI
from pydantic import BaseModel
from aerobotics.client import AeroboticsClient
from aerobotics.models import Survey, TreeSurvey, Page
from orchard_analysis.dualaxisscanner import DualAxisScanner
from orchard_analysis.geovector import Coordinate, Vector

# requests or httpx? Should I make this all asynchronous for speed? It probably doesn't matter for this demo.

app = FastAPI()

aerobotics_client = AeroboticsClient(
    base_url="https://api.aerobotics.com",
    api_key="4c80d904cae3d86b472fd636ef9d78a36faea104c61c7018a3604285d552d5e4"
)

# The response model for missing trees
class MissingTreesResponse(BaseModel):
        missing_trees: list[Coordinate]

@app.get("/orchards/{orchard_id}/missing-trees", response_model=MissingTreesResponse)
async def get_missing_trees(orchard_id: int):

    # Using the orchard_id, we can get the latest survey for the orchard.
    orchard_surveys: Page[Survey] = await aerobotics_client.get_multiple_surveys(orchard_id)

    # For now, let's just take the first survey.
    latest_orchard_survey: Survey = orchard_surveys.results[0]

    tree_surveys: Page[TreeSurvey] = await aerobotics_client.get_tree_surveys(latest_orchard_survey.id)

    # Retrieve the coordinates for all trees in the survey
    points = np.array([[tree.lat, tree.lng] for tree in tree_surveys.results])

    scanner = DualAxisScanner(points)
    missing_gps, missing_meters = scanner.solve()

    return MissingTreesResponse(missing_trees=[Coordinate(lat=tree[0], lng=tree[1]) for tree in missing_gps])


# Thinking about how to find missing trees here.

# For the orchard_analysis survey, we need to find the distance between each orchard_analysis and its nearest neighbor and probably on 2 axis (row and column).
# Once we find the median distance between trees, we can set a threshold (e.g., 1.5x median distance) to identify missing trees.
# For each orchard_analysis, we can check if there is another orchard_analysis within the threshold distance in both axes.
# If not, we can consider that position as a missing orchard_analysis.

# We could use a KD Tree but the data is already in a grid format so we don't need to know the row and column indices of each orchard_analysis to find missing trees.
