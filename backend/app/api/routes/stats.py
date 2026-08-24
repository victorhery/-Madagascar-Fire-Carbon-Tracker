import datetime

from fastapi import APIRouter, Depends

from app.repositories import (
    AlertRepositoryInterface,
    BurnedAreaRepositoryInterface,
    FireRepositoryInterface,
    get_alert_repository,
    get_burned_area_repository,
    get_fire_repository,
)
from app.schemas.stats import StatsSummary

router = APIRouter(prefix="/api/v1/stats", tags=["stats"])


@router.get("", response_model=StatsSummary)
def get_stats_summary(
    fire_repo: FireRepositoryInterface = Depends(get_fire_repository),
    burned_area_repo: BurnedAreaRepositoryInterface = Depends(get_burned_area_repository),
    alert_repo: AlertRepositoryInterface = Depends(get_alert_repository),
) -> StatsSummary:
    """
    Agrège les 3 repositories pour alimenter les StatCard du dashboard.
    Tant que la Phase 6 (GEE) n'existe pas, burned_area_hectares_total et
    co2_estimate_tons_total valent 0 -> normal, reflète l'état réel des données.
    """
    today = datetime.date.today()

    active_fires_24h = fire_repo.count_since(since=today - datetime.timedelta(days=1))

    counts_by_day = fire_repo.count_grouped_by_day(since=today - datetime.timedelta(days=6))
    trend = [counts_by_day.get(today - datetime.timedelta(days=i), 0) for i in range(6, -1, -1)]

    area_total, carbon_total = burned_area_repo.totals()
    active_alerts = alert_repo.count_active()

    return StatsSummary(
        active_fires_24h=active_fires_24h,
        active_fires_trend_7d=trend,
        burned_area_hectares_total=area_total,
        co2_estimate_tons_total=carbon_total,
        active_alerts=active_alerts,
    )
