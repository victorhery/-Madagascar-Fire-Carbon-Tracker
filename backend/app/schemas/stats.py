from typing import List

from pydantic import BaseModel


class StatsSummary(BaseModel):
    active_fires_24h: int
    active_fires_trend_7d: List[int]
    active_fires_trend_31d: List[int]
    burned_area_hectares_total: float
    co2_estimate_tons_total: float
    active_alerts: int