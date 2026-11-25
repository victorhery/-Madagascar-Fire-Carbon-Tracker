"""
Tâches de fond de la plateforme :

- polling NASA FIRMS toutes les 15 minutes ;
- estimation quotidienne de la surface brûlée et du carbone via
  Sentinel-2 et MODIS ;
- génération d'alertes.

Objectif : une ONG/entreprise déploie la plateforme avec une seule commande
(`uvicorn app.main:app` ou double-clic sur `start.bat`). Ce module est lancé
par le cycle de vie FastAPI dans `app/main.py`.
"""

import datetime
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.core.config import settings
from app.core.database import SessionLocal
from app.jobs.estimate_burned_area import run_estimate_burned_area_daily
from app.jobs.generate_alerts import run_generate_alerts
from app.jobs.poll_firms import run_poll_firms
from app.repositories import (
    SQLAlchemyAlertRepository,
    SQLAlchemyBurnedAreaRepository,
    SQLAlchemyFireRepository,
)
from app.services import (
    CarbonEstimationError,
    FirmsFetcherService,
    GeeCarbonEstimationService,
    Sentinel2CarbonEstimationService,
)

logger = logging.getLogger("scheduler")

DEFAULT_REGION_LABEL = "COFAV"

SENTINEL2_WINDOW_DAYS = 21
MODIS_WINDOW_DAYS = 120

FIRMS_POLL_INTERVAL_MINUTES = 15
CARBON_ESTIMATE_INTERVAL_HOURS = 24
ALERTS_INTERVAL_HOURS = 1


def _bbox() -> tuple[float, float, float, float]:
    west, south, east, north = (
        float(value) for value in settings.COFAV_BBOX.split(",")
    )
    return west, south, east, north


async def _poll_firms_job() -> None:
    """Récupère et enregistre les nouveaux hotspots FIRMS des dernières 24 h."""
    db = SessionLocal()

    try:
        fetcher = FirmsFetcherService(
            api_key=settings.NASA_MAP_KEY,
            bbox=settings.COFAV_BBOX,
        )
        repo = SQLAlchemyFireRepository(db)

        result = await run_poll_firms(
            fetcher=fetcher,
            repo=repo,
            day_range=1,
        )

        logger.info(
            "FIRMS : %s récupérées, %s créées, %s doublons ignorés",
            result.fetched,
            result.created,
            result.duplicates_skipped,
        )

        if result.created > 0:
            logger.info(
                "FIRMS : %s nouvelle(s) détection(s) VIIRS enregistrée(s). "
                "Surface brûlée et carbone : en attente d'une image "
                "Sentinel-2 post-feu exploitable.",
                result.created,
            )

    except Exception:
        logger.exception(
            "Erreur pendant le polling FIRMS "
            "(le scheduler continue de tourner)"
        )
    finally:
        db.close()


def _build_carbon_source(source_name: str):
    if source_name == "sentinel2":
        return Sentinel2CarbonEstimationService(
            service_account_json=settings.GEE_SERVICE_ACCOUNT_JSON,
            project_id=settings.GEE_PROJECT_ID,
        )

    return GeeCarbonEstimationService(
        service_account_json=settings.GEE_SERVICE_ACCOUNT_JSON,
        project_id=settings.GEE_PROJECT_ID,
    )


async def _estimate_carbon_job(
    source_name: str,
    window_days: int,
) -> None:
    db = SessionLocal()

    try:
        source = _build_carbon_source(source_name)
        repo = SQLAlchemyBurnedAreaRepository(db)
        today = datetime.date.today()

        created = run_estimate_burned_area_daily(
            source=source,
            repo=repo,
            region=DEFAULT_REGION_LABEL,
            bbox=_bbox(),
            period_start=today - datetime.timedelta(days=window_days),
            period_end=today,
            source_name=source_name,
        )

        if created:
            details = ", ".join(
                f"{item.period_start}:{item.area_hectares:.1f}ha"
                for item in created
            )
            logger.info(
                "%s : %d nouveau(x) jour(s) calculé(s) (%s)",
                source_name,
                len(created),
                details,
            )
        else:
            logger.info(
                "%s : aucune nouvelle surface brûlée calculée "
                "(pas encore d'image exploitable, jours déjà connus, "
                "ou aucune zone brûlée détectée)",
                source_name,
            )

    except CarbonEstimationError as exc:
        logger.warning("Erreur GEE (%s) : %s", source_name, exc)
    except Exception:
        logger.exception(
            "Erreur inattendue pendant l'estimation %s "
            "(le scheduler continue de tourner)",
            source_name,
        )
    finally:
        db.close()


async def _sentinel2_job() -> None:
    """Calcule les zones brûlées Sentinel-2 et le carbone associé."""
    await _estimate_carbon_job("sentinel2", SENTINEL2_WINDOW_DAYS)


async def _modis_job() -> None:
    """Conserve MODIS seulement pour l'historique et la comparaison."""
    await _estimate_carbon_job("modis", MODIS_WINDOW_DAYS)


async def _generate_alerts_job() -> None:
    db = SessionLocal()

    try:
        fire_repo = SQLAlchemyFireRepository(db)
        alert_repo = SQLAlchemyAlertRepository(db)

        alert = run_generate_alerts(
            fire_repo=fire_repo,
            alert_repo=alert_repo,
        )

        if alert is not None:
            logger.info(
                "Alerte active mise à jour : niveau=%s région=%s",
                alert.level.value,
                alert.region,
            )
    except Exception:
        logger.exception("Erreur pendant la génération d'alertes")
    finally:
        db.close()


def create_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()

    scheduler.add_job(
        _poll_firms_job,
        trigger="interval",
        minutes=FIRMS_POLL_INTERVAL_MINUTES,
        id="poll_firms",
        max_instances=1,
        coalesce=True,
    )

    scheduler.add_job(
        _sentinel2_job,
        trigger="interval",
        hours=CARBON_ESTIMATE_INTERVAL_HOURS,
        id="estimate_sentinel2",
        max_instances=1,
        coalesce=True,
    )

    scheduler.add_job(
        _modis_job,
        trigger="interval",
        hours=CARBON_ESTIMATE_INTERVAL_HOURS,
        id="estimate_modis",
        max_instances=1,
        coalesce=True,
    )

    scheduler.add_job(
        _generate_alerts_job,
        trigger="interval",
        hours=ALERTS_INTERVAL_HOURS,
        id="generate_alerts",
        max_instances=1,
        coalesce=True,
    )

    return scheduler


async def run_immediate_jobs() -> None:
    """
    Premier passage après le démarrage de l'API.

    Les tâches sont lancées par `asyncio.create_task()` dans `app/main.py`,
    afin que le démarrage d'Uvicorn ne soit pas bloqué par FIRMS ou GEE.
    """
    await _poll_firms_job()
    await _sentinel2_job()
    await _modis_job()
    await _generate_alerts_job()