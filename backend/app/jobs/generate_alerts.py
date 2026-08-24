from datetime import date, timedelta
from typing import Optional

from app.models import Alert, AlertLevel
from app.repositories import AlertRepositoryInterface, FireRepositoryInterface

# Zone par défaut utilisée tant qu'aucun rapprochement coordonnées -> région
# nommée n'existe côté backend (limite connue, voir PROGRESS.md Phase 6).
DEFAULT_REGION_LABEL = "COFAV"

# Nombre de détections sur la fenêtre analysée pour déclencher chaque niveau.
THRESHOLDS = {
    AlertLevel.HIGH: 30,
    AlertLevel.MEDIUM: 15,
    AlertLevel.LOW: 5,
}


def determine_alert_level(detection_count: int) -> Optional[AlertLevel]:
    """Seuils simples, ordonnés du plus sévère au moins sévère."""
    if detection_count >= THRESHOLDS[AlertLevel.HIGH]:
        return AlertLevel.HIGH
    if detection_count >= THRESHOLDS[AlertLevel.MEDIUM]:
        return AlertLevel.MEDIUM
    if detection_count >= THRESHOLDS[AlertLevel.LOW]:
        return AlertLevel.LOW
    return None


def run_generate_alerts(
    fire_repo: FireRepositoryInterface,
    alert_repo: AlertRepositoryInterface,
    region: str = DEFAULT_REGION_LABEL,
    window_days: int = 1,
) -> Optional[Alert]:
    """
    Compte les détections récentes et crée une alerte si un seuil est
    dépassé. Dépend uniquement des interfaces (principe D) -> testable
    sans base de données réelle.

    NOTE (limite connue) : faute de rapprochement coordonnées -> région
    nommée, l'alerte porte sur la zone COFAV entière, pas sur une commune
    précise (Ihorombe, Vatovavy...). Amélioration possible dans une phase
    ultérieure.
    """
    since = date.today() - timedelta(days=window_days)
    detection_count = fire_repo.count_since(since=since)

    level = determine_alert_level(detection_count)
    if level is None:
        return None

    alert = Alert(
        region=region,
        level=level,
        message=(
            f"{detection_count} détections de feu sur les dernières "
            f"{window_days * 24}h dans la zone {region}."
        ),
    )
    return alert_repo.create(alert)
