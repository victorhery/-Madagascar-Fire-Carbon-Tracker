from datetime import date
from typing import List, Tuple

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
    source_name: str = "modis",
) -> BurnedArea:
    """
    Version AGRÉGÉE (un seul blob pour toute la fenêtre) -> conservée pour
    les tests manuels ponctuels (run_estimate_burned_area_once.py sans
    --daily). Le scheduler automatique utilise désormais
    run_estimate_burned_area_daily ci-dessous.
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
        source=source_name,
    )

    return repo.create(burned_area)


def run_estimate_burned_area_daily(
    source: CarbonEstimationSourceInterface,
    repo: BurnedAreaRepositoryInterface,
    region: str,
    bbox: Tuple[float, float, float, float],
    period_start: date,
    period_end: date,
    source_name: str,
) -> List[BurnedArea]:
    """
    Version QUOTIDIENNE : persiste UNE ligne PAR JOUR détecté (period_start
    == period_end sur chaque ligne), jamais un blob agrégé. Dédoublonnée
    par (région, source, jour) -> rejouer une fenêtre qui chevauche des
    jours déjà connus ne crée aucun doublon (même principe que
    run_poll_firms pour les détections FIRMS). C'est cette fonction que le
    scheduler automatique appelle (voir app/core/scheduling.py).
    """
    daily_estimates = source.estimate_burned_area_daily(
        region=region, bbox=bbox, period_start=period_start, period_end=period_end
    )

    created: List[BurnedArea] = []
    for estimate in daily_estimates:
        existing = repo.get_by_natural_key(
            region=estimate.region, source=source_name,
            period_start=estimate.period_start, period_end=estimate.period_end,
        )
        if existing is not None:
            continue

        burned_area = BurnedArea(
            region=estimate.region,
            area_hectares=estimate.area_hectares,
            carbon_tons_estimate=estimate.carbon_tons_estimate,
            period_start=estimate.period_start,
            period_end=estimate.period_end,
            source=source_name,
        )
        created.append(repo.create(burned_area))

    return created
