from datetime import date, timedelta
from typing import Optional

from app.models import Alert, AlertLevel
from app.repositories import AlertRepositoryInterface, FireRepositoryInterface


DEFAULT_REGION_LABEL = "COFAV"

THRESHOLDS = {
    AlertLevel.HIGH: 30,
    AlertLevel.MEDIUM: 15,
    AlertLevel.LOW: 5,
}


def determine_alert_level(detection_count: int) -> Optional[AlertLevel]:
    if detection_count >= THRESHOLDS[AlertLevel.HIGH]:
        return AlertLevel.HIGH
    if detection_count >= THRESHOLDS[AlertLevel.MEDIUM]:
        return AlertLevel.MEDIUM
    if detection_count >= THRESHOLDS[AlertLevel.LOW]:
        return AlertLevel.LOW
    return None


def _build_alert_message(
    detection_count: int,
    window_days: int,
    region: str,
) -> str:
    return (
        f"{detection_count} détections de feu sur les dernières "
        f"{window_days * 24}h dans la zone {region}."
    )


def run_generate_alerts(
    fire_repo: FireRepositoryInterface,
    alert_repo: AlertRepositoryInterface,
    region: str = DEFAULT_REGION_LABEL,
    window_days: int = 1,
) -> Optional[Alert]:
    since = date.today() - timedelta(days=window_days)
    detection_count = fire_repo.count_since(since=since)

    level = determine_alert_level(detection_count)
    if level is None:
        return None

    message = _build_alert_message(
        detection_count=detection_count,
        window_days=window_days,
        region=region,
    )

    active_alert = alert_repo.get_active_by_region(region=region)

    if active_alert is not None:
        active_alert.level = level
        active_alert.message = message
        return alert_repo.update(active_alert)

    return alert_repo.create(
        Alert(
            region=region,
            level=level,
            message=message,
        )
    )