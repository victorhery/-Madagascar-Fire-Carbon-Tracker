"""
Lance une estimation GEE (surface brûlée + carbone) pour une région/bbox
donnée, et la sauvegarde en base. Nécessite un vrai GEE_SERVICE_ACCOUNT_JSON
dans ton .env (voir la documentation Google Earth Engine pour créer un
compte de service).

Usage (valeurs par défaut = zone COFAV entière, 16 derniers jours) :
    python run_estimate_burned_area_once.py
    python run_estimate_burned_area_once.py --region "Ihorombe" --days 30
"""
import argparse
import datetime

from app.core.config import settings
from app.core.database import SessionLocal
from app.jobs.estimate_burned_area import run_estimate_burned_area
from app.repositories import SQLAlchemyBurnedAreaRepository
from app.services import CarbonEstimationError, GeeCarbonEstimationService


def parse_bbox(bbox_str: str):
    # Même format que COFAV_BBOX dans config.py : "ouest,sud,est,nord"
    west, south, east, north = (float(x) for x in bbox_str.split(","))
    return (west, south, east, north)


def main(region: str, bbox_str: str, days: int) -> None:
    period_end = datetime.date.today()
    period_start = period_end - datetime.timedelta(days=days)

    db = SessionLocal()
    try:
        source = GeeCarbonEstimationService(service_account_json=settings.GEE_SERVICE_ACCOUNT_JSON)
        repo = SQLAlchemyBurnedAreaRepository(db)

        result = run_estimate_burned_area(
            source, repo,
            region=region, bbox=parse_bbox(bbox_str),
            period_start=period_start, period_end=period_end,
        )
        print(
            f"Terminé : région={result.region}, "
            f"surface={result.area_hectares:.2f} ha, "
            f"carbone={result.carbon_tons_estimate:.2f} tonnes"
        )
    except CarbonEstimationError as exc:
        print(f"Erreur GEE : {exc}")
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--region", type=str, default="COFAV")
    parser.add_argument("--bbox", type=str, default=None, help="Format: ouest,sud,est,nord")
    parser.add_argument("--days", type=int, default=16, help="Période analysée (jours en arrière)")
    args = parser.parse_args()

    bbox_value = args.bbox or settings.COFAV_BBOX
    main(region=args.region, bbox_str=bbox_value, days=args.days)
