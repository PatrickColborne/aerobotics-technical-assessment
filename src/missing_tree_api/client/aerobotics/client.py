import httpx
from .models import Survey, Page, TreeSurveySummary, TreeSurvey


class AeroboticsClient:
    """
    Asynchronous client for interacting with the Aerobotics API.
    """
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip("/")
        self.__common_headers = {
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json"
        }

    async def _get(self, path: str, headers: dict = None, params: dict = None):
        """ Utility method to containing boilerplate for GET requests """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}{path}",
                headers={**self.__common_headers, **(headers or {})},
                params=params,
                timeout=10.0,
            )
            response.raise_for_status()
            return response.json()

    async def get_multiple_surveys(self, orchard_id: int, limit: int = 100, offset: int = 0) -> Page[Survey]:
        """Returns survey records for some filtered set of surveys"""
        params = {"orchard_id": orchard_id, "limit": limit, "offset": offset}
        data = await self._get("/farming/surveys", params=params)
        return Page[Survey].model_validate(data)

    async def get_survey(self, survey_id: int) -> Survey:
        """Returns the survey record for a single survey"""
        data = await self._get(f"/farming/surveys/{survey_id}")
        return Survey.model_validate(data)

    async def get_tree_survey_summary(self, survey_id: int) -> TreeSurveySummary:
        """Get a tree survey summary for a survey"""
        data = await self._get(f"/farming/surveys/{survey_id}/tree_survey_summaries")
        return TreeSurveySummary.model_validate(data)

    async def get_tree_surveys(self, survey_id: int, limit: int = 100, offset: int = 0) -> Page[TreeSurvey]:
        """Get tree surveys for a survey"""
        params = { "limit": limit, "offset": offset }
        data = await self._get(f"/farming/surveys/{survey_id}/tree_surveys", params=params)
        return Page[TreeSurvey].model_validate(data)
