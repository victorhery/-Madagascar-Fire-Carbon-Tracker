from typing import List

from pydantic import BaseModel


class StatsSummary(BaseModel):
    """
    Alimente les StatCard du dashboard (feux actifs, surface brûlée, CO2,
    alertes). Tant que la Phase 6 (GEE) n'est pas faite, burned_area et
    co2 resteront à 0 -> normal, pas un bug.
    """

    active_fires_24h: int
    active_fires_trend_7d: List[int]
    burned_area_hectares_total: float
    co2_estimate_tons_total: float
    active_alerts: int
