from typing import List

from fastapi import APIRouter, Depends

from app.repositories import AlertRepositoryInterface, get_alert_repository
from app.schemas.alert import AlertOut

router = APIRouter(prefix="/api/v1/alerts", tags=["alerts"])


@router.get("/active", response_model=List[AlertOut])
def list_active_alerts(
    repo: AlertRepositoryInterface = Depends(get_alert_repository),
) -> List[AlertOut]:
    return repo.list_active()
