import datetime
from typing import List

from fastapi import APIRouter, Depends

from app.repositories import BurnedAreaRepositoryInterface, get_burned_area_repository
from app.schemas.carbon import BurnedAreaOut

router = APIRouter(prefix="/api/v1/carbon", tags=["carbon"])


@router.get("/estimates", response_model=List[BurnedAreaOut])
def list_carbon_estimates(
    since_days: int = 30,
    repo: BurnedAreaRepositoryInterface = Depends(get_burned_area_repository),
) -> List[BurnedAreaOut]:
    """
    Liste les estimations GEE récentes (surface brûlée + carbone).
    Vide tant que la Phase 6 n'a pas été exécutée en vrai -> normal.
    """
    since = datetime.date.today() - datetime.timedelta(days=since_days)
    return repo.list_recent(since=since)
