import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends

from app.repositories import BurnedAreaRepositoryInterface, get_burned_area_repository
from app.schemas.carbon import BurnedAreaOut

router = APIRouter(prefix="/api/v1/carbon", tags=["carbon"])


@router.get("/estimates", response_model=List[BurnedAreaOut])
def list_carbon_estimates(
    since_days: int = 30,
    repo: BurnedAreaRepositoryInterface = Depends(get_burned_area_repository),
) -> List[BurnedAreaOut]:
    """Liste BRUTE de tous les runs (y compris les anciens scans par
    fenêtre) -> usage debug/admin. Pour l'affichage dashboard, voir /history."""
    since = datetime.date.today() - datetime.timedelta(days=since_days)
    return repo.list_recent(since=since)


@router.get("/current", response_model=List[BurnedAreaOut])
def list_current_carbon_estimates(
    repo: BurnedAreaRepositoryInterface = Depends(get_burned_area_repository),
) -> List[BurnedAreaOut]:
    """Une ligne par région/source (dernier résultat connu, y compris les
    anciens scans par fenêtre) -> conservé pour compatibilité."""
    return repo.latest_by_region_and_source()


@router.get("/history", response_model=List[BurnedAreaOut])
def list_carbon_history(
    since_days: int = 90,
    region: Optional[str] = None,
    repo: BurnedAreaRepositoryInterface = Depends(get_burned_area_repository),
) -> List[BurnedAreaOut]:
    """
    Historique JOUR PAR JOUR : chaque ligne = un jour où une combustion a
    été détectée par un satellite précis (period_start == period_end),
    triées du plus récent au plus ancien. C'est CET endpoint que le
    dashboard utilise -> vraie détection incrémentale, jamais les anciens
    scans par fenêtre de plusieurs semaines.
    """
    since = datetime.date.today() - datetime.timedelta(days=since_days)
    return repo.list_daily_history(since=since, region=region)
