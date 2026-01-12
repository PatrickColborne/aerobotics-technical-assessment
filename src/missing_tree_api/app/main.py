import logging
import os
from typing import Optional, List

import httpx
from fastapi import FastAPI, HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from missing_tree_api.client.aerobotics.client import AeroboticsClient
from missing_tree_api.client.aerobotics.models import Page, Survey, TreeSurvey
from missing_tree_api.core.orchardscanner import OrchardScanner
from missing_tree_api.models.schemas import MissingTreesResponse

# Configure logging to see errors in your console/logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Client
# Note: In a real app, strict validation of env vars at startup is better than defaults
aerobotics_client = AeroboticsClient(
    base_url=os.getenv("AEROBOTICS_BASE_URL", "https://api.aerobotics.com"),
    api_key=os.getenv("AEROBOTICS_API_KEY")
)

security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    """
    Validates the Bearer token from the Authorization header.
    """
    token = credentials.credentials

    # Just 1 token for simplicity; in real apps, consider more robust auth
    expected_token = os.getenv("API_KEY")

    if token != expected_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token

app = FastAPI(title="Missing Tree Finder")

@app.get(
    "/orchards/{orchard_id}/missing-trees",
    response_model=MissingTreesResponse,
    responses={
        404: {"description": "Orchard or Survey not found"},
        502: {"description": "Upstream API error"},
        500: {"description": "Internal Server Error"}
    }
)
async def get_missing_trees(orchard_id: int, token: str = Security(verify_token)) -> MissingTreesResponse:
    logger.info(f"Analyzing orchard {orchard_id}...")

    # 1. Get Surveys
    try:
        latest_survey = await _get_latest_survey(orchard_id=orchard_id)
    except Exception as e:
        # Log the actual trace for debugging, return a generic error to user
        logger.error(f"Failed to fetch surveys for orchard {orchard_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to retrieve survey data from upstream provider."
        )

    if latest_survey is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No surveys found for orchard ID {orchard_id}"
        )

    # 2. Get Trees
    try:
        trees = await _get_all_tree_locations_in_survey(survey_id=latest_survey.id)
    except Exception as e:
        logger.error(f"Failed to fetch trees for survey {latest_survey.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to retrieve tree data from upstream provider."
        )

    if not trees:
        return MissingTreesResponse(missing_trees=[])

    # 3. Analyze
    try:
        # Offload CPU-heavy work if the dataset is massive (optional optimization)
        missing_trees = _find_missing_trees(trees)
    except Exception as e:
        logger.error(f"Algorithm failed for orchard {orchard_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error analyzing orchard structure."
        )

    return MissingTreesResponse(
        missing_trees=[{"lat": tree[0], "lng": tree[1]} for tree in missing_trees]
    )


async def _get_all_surveys(orchard_id: int) -> List[Survey]:
    """Get all surveys for an orchard, handling pagination and API errors."""
    limit = 100
    offset = 0
    surveys = []

    while True:
        try:
            response: Page[Survey] = await aerobotics_client.get_multiple_surveys(
                orchard_id=orchard_id, limit=limit, offset=offset
            )
        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            # Re-raise so the caller can handle it or log it specifically here
            logger.error(f"Upstream API error fetching surveys (offset {offset}): {e}")
            raise e

        if not response or not response.results:
            break

        surveys.extend(response.results)

        # SAFETY CHECK: Ensure we don't loop forever if 'count' isn't what we expect
        # Usually checking len(results) is safer than relying on a .count attribute
        if len(response.results) < limit:
            break

        offset += limit

    return surveys


async def _get_latest_survey(orchard_id: int) -> Optional[Survey]:
    """Get the latest survey. Returns None if no surveys found."""
    surveys = await _get_all_surveys(orchard_id)

    if not surveys:
        return None

    # Filter out surveys that might have missing dates to prevent crashes
    valid_surveys = [s for s in surveys if getattr(s, 'date', None)]

    if not valid_surveys:
        return None

    # Now it is safe to use max()
    return max(valid_surveys, key=lambda s: s.date)


async def _get_all_tree_locations_in_survey(survey_id: int) -> List[List[float]]:
    """Get all trees, handling pagination and API errors."""
    limit = 500
    offset = 0
    trees = []

    while True:
        try:
            tree_surveys: Page[TreeSurvey] = await aerobotics_client.get_tree_surveys(
                survey_id=survey_id, limit=limit, offset=offset
            )
        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            logger.error(f"Upstream API error fetching trees (offset {offset}): {e}")
            raise e

        if not tree_surveys or not tree_surveys.results:
            break

        # Validate data integrity: Ensure lat/lng actually exist
        valid_trees = [
            [t.lat, t.lng] for t in tree_surveys.results
            if t.lat is not None and t.lng is not None
        ]
        trees.extend(valid_trees)

        if len(tree_surveys.results) < limit:
            break

        offset += limit

    return trees

def _find_missing_trees(trees: List[List[float]]) -> List[List[float]]:
    if not trees:
        return []

    scanner = OrchardScanner(trees)
    missing_trees, _ = scanner.solve()
    return missing_trees
