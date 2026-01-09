import httpx
from .models import Survey, Page, TreeSurveySummary, TreeSurvey
from typing import List


class AeroboticsClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip("/")
        self.headers = {"Authorization": f"Bearer {api_key}"}

    async def _get(self, path: str, params: dict = None):
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}{path}",
                headers=self.headers,
                params=params,
                timeout=10.0,
            )
            response.raise_for_status()
            return response.json()

    async def get_survey(self, survey_id: int) -> Survey:
        data = await self._get(f"/farming/surveys/{survey_id}")
        return Survey.model_validate(data)

    async def get_multiple_surveys(
            self, orchard_id: int, limit: int = 100, offset: int = 0
    ) -> Page[Survey]:
        params = {"orchard_id": orchard_id, "limit": limit, "offset": offset}
        data = await self._get("/farming/surveys", params=params)
        return Page[Survey].model_validate(data)

    async def get_tree_survey_summary(self, survey_id: int) -> TreeSurveySummary:
        data = await self._get(f"/farming/surveys/{survey_id}/tree_survey_summaries")
        return TreeSurveySummary.model_validate(data)

    async def get_tree_surveys(self, survey_id: int) -> Page[TreeSurvey]:
        data = await self._get(f"/farming/surveys/{survey_id}/tree_surveys")
        return Page[TreeSurvey].model_validate(data)
