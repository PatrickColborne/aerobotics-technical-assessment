import httpx
from .models import Survey, Page, TreeSurveySummary, TreeSurvey
from typing import List, Optional


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
    #
    # async def get_tree_surveys(self, survey_id: int, limit: int = 100, offset: int = 0) -> Page[TreeSurvey]:
    #     params = { "limit": limit, "offset": offset }
    #     data = await self._get(f"/farming/surveys/{survey_id}/tree_surveys", params=params)
    #     return Page[TreeSurvey].model_validate(data)

    async def get_tree_surveys(self, survey_id: int) -> Page[TreeSurvey]:
        data = await self._get(f"/farming/surveys/{survey_id}/tree_surveys")
        return Page[TreeSurvey].model_validate(data)
    #
    # async def get_all_tree_surveys(self, survey_id: int) -> List[TreeSurvey]:
    #     # Follow `next` until exhausted, aggregating results
    #     results: List[TreeSurvey] = []
    #
    #     # Start with the first page
    #     page = await self.get_tree_surveys(survey_id)
    #     results.extend(page.results or [])
    #
    #     print(page)
    #
    #     # While there is a `next` URL, fetch and append
    #     next_url: Optional[str] = page.next
    #     while next_url:
    #         data = await self._get(next_url)
    #         page = Page[TreeSurvey].model_validate(data)
    #         results.extend(page.results or [])
    #         next_url = page.next
    #
    #     return results