import os
from typing import Optional

from fastapi import FastAPI, HTTPException

from missing_tree_api.client.aerobotics.client import AeroboticsClient
from missing_tree_api.models.schemas import MissingTreesResponse

from missing_tree_api.client.aerobotics.models import Page, Survey, TreeSurvey
from missing_tree_api.core.dualaxisscanner import OrchardScanner

aerobotics_client = AeroboticsClient(
    base_url=os.getenv("AEROBOTICS_BASE_URL", "https://api.aerobotics.com"),
    api_key=os.getenv("AEROBOTICS_API_KEY")
)
app = FastAPI(title="Missing Tree Finder")


@app.get(
    "/orchards/{orchard_id}/missing-trees",
    response_model=MissingTreesResponse
)
async def get_missing_trees(orchard_id: int) -> MissingTreesResponse:

    # First get the latest survey for the orchard
    latest_survey = await _get_latest_survey(orchard_id=orchard_id)

    # Retrieve the tree surveys from the latest survey
    if latest_survey is None:
        raise HTTPException(status_code=404, detail="Survey not found")

    trees = await _get_all_tree_locations_in_survey(survey_id=latest_survey.id)

    if not trees:
        raise HTTPException(status_code=404, detail="Survey not found")

    # Analyze the tree surveys to find missing trees
    missing_trees = find_missing_trees(trees)

    # Return the missing trees
    return MissingTreesResponse(missing_trees=[ {"lat": tree[0], "lng": tree[1]} for tree in missing_trees ])

async def _get_all_surveys(orchard_id: int) -> list[Survey]:
    """Get all surveys for an orchard"""
    limit = 100
    offset = 0
    surveys = []
    while True:
        response: Page[Survey] = await aerobotics_client.get_multiple_surveys(orchard_id=orchard_id, limit=limit, offset=offset)
        if not response or not response.results:
            break
        surveys.extend(response.results)
        if response.count < limit:
            break
        offset += limit
    # Return the latest survey id if available
    return surveys

async def _get_latest_survey(orchard_id: int) -> Optional[Survey]:
    """Get the latest survey for an orchard based on the survey date"""
    surveys = await _get_all_surveys(orchard_id)
    if not surveys:
        return None
    # Assuming each Survey has a 'date' attribute in ISO format
    latest_survey = max(surveys, key=lambda s: getattr(s, "date", ""))
    return latest_survey

async def _get_all_tree_locations_in_survey(survey_id: int):
    """Get all tree coordinates for a given survey"""
    limit = 500
    offset = 0
    trees = []
    while True:
        tree_surveys: Page[TreeSurvey] = await aerobotics_client.get_tree_surveys(survey_id=survey_id, limit=limit, offset=offset)
        if not tree_surveys or not tree_surveys.results:
            break
        trees.extend([[tree.lat, tree.lng] for tree in tree_surveys.results])
        if tree_surveys.count < limit:
            break
        offset += limit
    return trees

def find_missing_trees(trees):
    scanner = OrchardScanner(trees)
    missing_gps, missing_meters = scanner.solve()
    return missing_gps
