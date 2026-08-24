from datetime import date
from typing import Tuple

from app.models import BurnedArea
from app.repositories import BurnedAreaRepositoryInterface
from app.services import CarbonEstimationSourceInterface


def run_estimate_burned_area(
    source: CarbonEstimationSourceInterface,
    repo: BurnedAreaRepositoryInterface,
    region: str,
    bbox: Tuple[float, float, float, float],
    period_start: date,
    period_end: date,
) -> BurnedArea:
    """
    Demande une estimation à `source` (GEE), puis la sauvegarde via `repo`.
    Dépend uniquement des deux interfaces (principe D) -> testable avec de
    purs mocks, sans réseau ni base de données réelle, comme run_poll_firms.

    NOTE : contrairement à run_poll_firms (qui balaie automatiquement toute
    la zone COFAV), cette fonction traite UNE région/bbox à la fois, fournie
    explicitement par l'appelant. La détection automatique de "quelles
    régions ont eu des feux récemment" nécessiterait un rapprochement
    coordonnées -> région qui n'existe pas encore côté backend (seul le
    frontend connaît COFAV_CITIES/COFAV_POLYGON) -> à construire dans une
    phase ultérieure si besoin.
    """
    estimate = source.estimate_burned_area(
        region=region, bbox=bbox, period_start=period_start, period_end=period_end
    )

    burned_area = BurnedArea(
        region=estimate.region,
        area_hectares=estimate.area_hectares,
        carbon_tons_estimate=estimate.carbon_tons_estimate,
        period_start=estimate.period_start,
        period_end=estimate.period_end,
    )

    return repo.create(burned_area)
