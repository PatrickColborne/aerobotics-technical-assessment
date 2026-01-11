from datetime import date
from typing import Generic, List, TypeVar, Optional

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
    tree_count: Optional[int] = None
    missing_tree_count: Optional[int] = None
    average_area_m2: Optional[float] = None
    stddev_area_m2: Optional[float] = None
    average_ndre: Optional[float] = None
    stddev_ndre: Optional[float] = None

class TreeSurvey(BaseModel):
    id: int
    lat: Optional[float] = None
    lng: Optional[float] = None
    ndre: Optional[float] = None
    ndvi: Optional[float] = None
    volume: Optional[float] = None
    area: Optional[float] = None
    row_index: Optional[int] = None
    tree_index: Optional[int] = None
    survey_id: int

class Page(BaseModel, Generic[T]):
    count: int
    next: Optional[str] = None
    previous: Optional[str] = None
    results: List[T]
