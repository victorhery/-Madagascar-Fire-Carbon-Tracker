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
    burned_area_repo: BurnedAreaRepositoryInterface = Depends(
        get_burned_area_repository
    ),
    alert_repo: AlertRepositoryInterface = Depends(get_alert_repository),
) -> StatsSummary:
    today = datetime.date.today()
    start_date = today - datetime.timedelta(days=30)

    active_fires_24h = fire_repo.count_since(
        since=today - datetime.timedelta(days=1)
    )

    counts_by_day = fire_repo.count_grouped_by_day(
        since=start_date
    )

    trend_31d = [
        counts_by_day.get(
            start_date + datetime.timedelta(days=offset),
            0,
        )
        for offset in range(31)
    ]

    area_total, carbon_total = (
        burned_area_repo.totals_latest_daily_per_region()
    )

    active_alerts = alert_repo.count_active()

    return StatsSummary(
        active_fires_24h=active_fires_24h,
        active_fires_trend_7d=trend_31d[-7:],
        active_fires_trend_31d=trend_31d,
        burned_area_hectares_total=area_total,
        co2_estimate_tons_total=carbon_total,
        active_alerts=active_alerts,
    )