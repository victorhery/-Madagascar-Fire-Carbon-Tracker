from typing import List, Optional

from pydantic import BaseModel


class FireFeatureProperties(BaseModel):
    brightness: Optional[float] = None
    confidence: Optional[str] = None
    acq_date: str
    acq_time: str
    frp: Optional[float] = None


class FireGeometry(BaseModel):
    type: str = "Point"
    coordinates: List[float]  # [longitude, latitude], convention GeoJSON


class FireFeature(BaseModel):
    type: str = "Feature"
    geometry: FireGeometry
    properties: FireFeatureProperties


class FireFeatureCollection(BaseModel):
    """
    Reprend exactement la forme attendue par frontend/src/services/fireService.ts
    (FireFeatureCollection) -> aucun changement necessaire côté frontend
    quand on branchera cet endpoint en Phase 8.
    """

    type: str = "FeatureCollection"
    features: List[FireFeature]
