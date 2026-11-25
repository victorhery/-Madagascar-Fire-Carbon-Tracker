"""
Lance une estimation GEE (surface brûlée + carbone) pour une région/bbox
donnée, et la sauvegarde en base.

2 modes de sortie :
- Par défaut : UN blob agrégé pour toute la fenêtre (comportement d'origine,
  pratique pour un test rapide "est-ce qu'il y a quelque chose ?").
- --daily : UNE ligne par jour détecté, dédoublonnée (même logique que le
  scheduler automatique) -> pour vérifier concrètement la détection
  jour par jour avant de faire confiance au dashboard.

2 sources disponibles (--source) :
- modis (défaut) : MCD64A1, 500m, validé scientifiquement, ~2-3 mois de délai
- sentinel2 : dNBR maison, 10-20m, quelques jours de délai, estimation
  indicative (seuil non calibré sur le COFAV pour l'instant)

Usage :
    python run_estimate_burned_area_once.py
    python run_estimate_burned_area_once.py --source sentinel2 --days 21
    python run_estimate_burned_area_once.py --source sentinel2 --days 21 --daily
    python run_estimate_burned_area_once.py --source modis --period-start 2026-06-01 --period-end 2026-09-15 --daily
"""
import argparse
import datetime

from app.core.config import settings
from app.core.database import SessionLocal
from app.jobs.estimate_burned_area import run_estimate_burned_area, run_estimate_burned_area_daily
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


def main(
    region: str, bbox_str: str, period_start_str: str, period_end_str: str,
    source_name: str, daily: bool,
) -> None:
    period_start = datetime.date.fromisoformat(period_start_str)
    period_end = datetime.date.fromisoformat(period_end_str)

    db = SessionLocal()
    try:
        source = build_source(source_name)
        repo = SQLAlchemyBurnedAreaRepository(db)

        if daily:
            created = run_estimate_burned_area_daily(
                source, repo,
                region=region, bbox=parse_bbox(bbox_str),
                period_start=period_start, period_end=period_end,
                source_name=source_name,
            )
            if not created:
                print(
                    f"Terminé ({source_name}, --daily) : aucun nouveau jour "
                    f"(déjà en base, ou 0 combustion sur {period_start} -> {period_end})."
                )
            else:
                print(f"Terminé ({source_name}, --daily) : {len(created)} nouveau(x) jour(s) :")
                for row in created:
                    print(f"  {row.period_start} : {row.area_hectares:.2f} ha, {row.carbon_tons_estimate:.2f} tonnes")
        else:
            result = run_estimate_burned_area(
                source, repo,
                region=region, bbox=parse_bbox(bbox_str),
                period_start=period_start, period_end=period_end,
                source_name=source_name,
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
    parser.add_argument("--daily", action="store_true", help="Extraction jour par jour au lieu d'un blob agrégé")
    args = parser.parse_args()

    bbox_value = args.bbox or settings.COFAV_BBOX

    if args.period_start and args.period_end:
        start_str, end_str = args.period_start, args.period_end
    else:
        days = args.days or 16
        end_str = datetime.date.today().isoformat()
        start_str = (datetime.date.today() - datetime.timedelta(days=days)).isoformat()

    main(
        region=args.region, bbox_str=bbox_value,
        period_start_str=start_str, period_end_str=end_str,
        source_name=args.source, daily=args.daily,
    )
