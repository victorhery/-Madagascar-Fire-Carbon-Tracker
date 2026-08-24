"""
Lance le polling périodique de NASA FIRMS, INDÉPENDAMMENT de l'API FastAPI
(même principe que create_tables.py : pas de couplage avec `uvicorn app.main:app`).

Ce script doit rester ouvert dans son propre terminal, en parallèle de l'API.

Usage :
    python run_poll_firms_scheduler.py
Arrêt : Ctrl+C dans ce terminal.
"""
import asyncio
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.core.config import settings
from app.core.database import SessionLocal
from app.jobs.poll_firms import run_poll_firms
from app.repositories import SQLAlchemyFireRepository
from app.services import FirmsFetcherService

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("poll_firms_scheduler")

# FIRMS se met à jour environ toutes les 3h -> on interroge à la même cadence.
POLL_INTERVAL_HOURS = 3


async def _run_once() -> None:
    """Une exécution du job : ouvre sa propre session DB, l'referme à la fin."""
    db = SessionLocal()
    try:
        fetcher = FirmsFetcherService(api_key=settings.NASA_MAP_KEY, bbox=settings.COFAV_BBOX)
        repo = SQLAlchemyFireRepository(db)
        result = await run_poll_firms(fetcher, repo, day_range=1)
        logger.info(
            "Polling FIRMS terminé : %s récupérées, %s créées, %s doublons ignorés",
            result.fetched, result.created, result.duplicates_skipped,
        )
    except Exception:
        logger.exception("Erreur pendant le polling FIRMS (le scheduler continue de tourner)")
    finally:
        db.close()


async def main() -> None:
    scheduler = AsyncIOScheduler()
    scheduler.add_job(_run_once, "interval", hours=POLL_INTERVAL_HOURS)
    scheduler.start()
    logger.info("Scheduler démarré (toutes les %sh). Ctrl+C pour arrêter.", POLL_INTERVAL_HOURS)

    await _run_once()  # premier passage immédiat, sans attendre 3h

    try:
        while True:
            await asyncio.sleep(3600)
    except (KeyboardInterrupt, SystemExit):
        logger.info("Arrêt du scheduler...")
        scheduler.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
