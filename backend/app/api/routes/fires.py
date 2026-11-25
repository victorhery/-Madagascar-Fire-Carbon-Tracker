import datetime

from fastapi import APIRouter, Depends

from app.repositories import FireRepositoryInterface, get_fire_repository
from app.schemas.fire import (
    FireFeature,
    FireFeatureCollection,
    FireFeatureProperties,
    FireGeometry,
)

router = APIRouter(prefix="/api/v1/fires", tags=["fires"])


@router.get("/recent", response_model=FireFeatureCollection)
def get_recent_fires(
    day_range: int = 1,
    repo: FireRepositoryInterface = Depends(get_fire_repository),
) -> FireFeatureCollection:
    """
    Lit les détections stockées en base, alimentée automatiquement par
    le polling NASA FIRMS. Le frontend n'appelle jamais FIRMS directement.
    """
    since = datetime.date.today() - datetime.timedelta(days=day_range)
    detections = repo.list_recent(since=since)

    features = [
        FireFeature(
            geometry=FireGeometry(
                coordinates=[detection.longitude, detection.latitude]
            ),
            properties=FireFeatureProperties(
                brightness=detection.brightness,
                confidence=detection.confidence,
                acq_date=detection.acq_date.isoformat(),
                acq_time=detection.acq_time,
                frp=detection.frp,
                satellite=detection.satellite,
            ),
        )
        for detection in detections
    ]

    return FireFeatureCollection(features=features)