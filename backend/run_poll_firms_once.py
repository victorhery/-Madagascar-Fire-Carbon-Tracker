"""
Exécute une seule fois le polling FIRMS (pratique en développement pour
peupler la base sans laisser tourner le scheduler en continu).

Usage :
    python run_poll_firms_once.py
    python run_poll_firms_once.py --day-range 3
"""
import argparse
import asyncio

from app.core.config import settings
from app.core.database import SessionLocal
from app.jobs.poll_firms import run_poll_firms
from app.repositories import SQLAlchemyFireRepository
from app.services import FirmsFetcherService


async def main(day_range: int) -> None:
    db = SessionLocal()
    try:
        fetcher = FirmsFetcherService(api_key=settings.NASA_MAP_KEY, bbox=settings.COFAV_BBOX)
        repo = SQLAlchemyFireRepository(db)
        result = await run_poll_firms(fetcher, repo, day_range=day_range)
        print(
            f"Terminé : {result.fetched} récupérées, {result.created} créées, "
            f"{result.duplicates_skipped} doublons ignorés."
        )
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--day-range", type=int, default=1)
    args = parser.parse_args()
    asyncio.run(main(args.day_range))
