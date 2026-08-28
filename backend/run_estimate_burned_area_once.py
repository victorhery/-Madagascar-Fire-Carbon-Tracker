"""
Lance une estimation GEE (surface brûlée + carbone) pour une région/bbox
donnée, et la sauvegarde en base.

Fonctionne avec les 2 modes configurés dans .env :
- GEE_SERVICE_ACCOUNT_JSON renseigné -> mode compte de service (production/ONG)
- GEE_PROJECT_ID renseigné seul -> mode authentification personnelle (dev local,
  nécessite d'avoir lancé `earthengine authenticate` une fois dans ce venv)

2 sources disponibles (--source) :
- modis (défaut) : MCD64A1, 500m, validé scientifiquement, ~2-3 mois de délai
- sentinel2 : dNBR maison, 10-20m, quelques jours de délai, estimation
  indicative (seuil non calibré sur le COFAV pour l'instant)

Usage (valeurs par défaut = zone COFAV entière, 16 derniers jours, MODIS) :
    python run_estimate_burned_area_once.py
    python run_estimate_burned_area_once.py --source sentinel2 --days 30
    python run_estimate_burned_area_once.py --region "Ihorombe" --days 30
"""
import argparse
import datetime

from app.core.config import settings
from app.core.database import SessionLocal
from app.jobs.estimate_burned_area import run_estimate_burned_area
from app.repositories import SQLAlchemyBurnedAreaRepository
from app.services import (
    CarbonEstimationError,
    GeeCarbonEstimationService,
    Sentinel2CarbonEstimationService,
)


def parse_bbox(bbox_str: str):
    west, south, east, north = (float(x) for x in bbox_str.split(","))
    return (west, south, east, north)


def build_source(source_name: str):
    if source_name == "sentinel2":
        return Sentinel2CarbonEstimationService(
            service_account_json=settings.GEE_SERVICE_ACCOUNT_JSON,
            project_id=settings.GEE_PROJECT_ID,
        )
    return GeeCarbonEstimationService(
        service_account_json=settings.GEE_SERVICE_ACCOUNT_JSON,
        project_id=settings.GEE_PROJECT_ID,
    )


def main(region: str, bbox_str: str, period_start_str: str, period_end_str: str, source_name: str) -> None:
    period_start = datetime.date.fromisoformat(period_start_str)
    period_end = datetime.date.fromisoformat(period_end_str)

    db = SessionLocal()
    try:
        source = build_source(source_name)
        repo = SQLAlchemyBurnedAreaRepository(db)

        result = run_estimate_burned_area(
            source, repo,
            region=region, bbox=parse_bbox(bbox_str),
            period_start=period_start, period_end=period_end,
        )
        print(
            f"Terminé ({source_name}) : région={result.region}, "
            f"période={period_start} -> {period_end}, "
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
    parser.add_argument("--days", type=int, default=None, help="Période analysée (jours en arrière depuis aujourd'hui)")
    parser.add_argument("--period-start", type=str, default=None, help="Format: YYYY-MM-DD (prioritaire sur --days)")
    parser.add_argument("--period-end", type=str, default=None, help="Format: YYYY-MM-DD (prioritaire sur --days)")
    parser.add_argument("--source", choices=["modis", "sentinel2"], default="modis")
    args = parser.parse_args()

    bbox_value = args.bbox or settings.COFAV_BBOX

    if args.period_start and args.period_end:
        start_str, end_str = args.period_start, args.period_end
    else:
        # MCD64A1 a un délai de publication réel d'environ 2-3 mois (vérifié
        # sur le catalogue GEE en août 2026, bien plus que les 5-16 jours
        # supposés au départ) -> "aujourd'hui - days" tombe souvent sur une
        # période sans donnée publiée. --period-start/--period-end explicites
        # sont plus fiables pour tester.
        days = args.days or 16
        end_str = datetime.date.today().isoformat()
        start_str = (datetime.date.today() - datetime.timedelta(days=days)).isoformat()

    main(region=args.region, bbox_str=bbox_value, period_start_str=start_str, period_end_str=end_str, source_name=args.source)
