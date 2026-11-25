from typing import List, Optional

from pydantic import BaseModel


class FireFeatureProperties(BaseModel):
    brightness: Optional[float] = None
    confidence: Optional[str] = None
    acq_date: str
    acq_time: str
    frp: Optional[float] = None
    satellite: str


class FireGeometry(BaseModel):
    type: str = "Point"
    coordinates: List[float]


class FireFeature(BaseModel):
    type: str = "Feature"
    geometry: FireGeometry
    properties: FireFeatureProperties


class FireFeatureCollection(BaseModel):
    type: str = "FeatureCollection"
    features: List[FireFeature]