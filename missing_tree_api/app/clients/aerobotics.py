import httpx
from pydantic import BaseModel
from datetime import date
from typing import List

class Survey(BaseModel):
    id: int
    orchard_id: int
    date: date
    hectares: float
    polygon: str

class Surveys(BaseModel):
    count: int
    next: str
    previous: str
    results: List[Survey]

class TreeSurveySummary(BaseModel):
    survey_id: int
    tree_count: int
    missing_tree_count: int
    average_area_m2: float
    stddev_area_m2: float
    average_ndre: float
    stddev_ndre: float

class TreeSurvey(BaseModel):
    id: int
    lat: float
    lng: float
    ndre: float
    ndvi: float
    volume: float
    area: float
    row_index: int
    tree_index: int
    survey_id: int


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
    ) -> Surveys:
        params = {"orchard_id": orchard_id, "limit": limit, "offset": offset}
        data = await self._get("/farming/surveys", params=params)
        return Surveys.model_validate(data)

    async def get_tree_survey_summary(self, survey_id: int) -> TreeSurveySummary:
        data = await self._get(f"/farming/surveys/{survey_id}/tree-survey-summaries")
        return TreeSurveySummary.model_validate(data)

    async def get_tree_surveys(self, survey_id: int) -> List[TreeSurvey]:
        data = await self._get(f"/farming/surveys/{survey_id}/tree-surveys")
        return [TreeSurvey.model_validate(item) for item in data]
