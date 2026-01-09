from datetime import date
from typing import Generic, List, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)

class Survey(BaseModel):
    id: int
    orchard_id: int
    date: date
    hectares: float
    polygon: str

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

class Page(BaseModel, Generic[T]):
    count: int
    next: str
    previous: str
    results: List[T]

# Aliases for typed pages
SurveyPage: Page[Survey]
TreeSurveyPage: Page[TreeSurvey]
