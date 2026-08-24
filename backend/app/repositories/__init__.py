from app.repositories.fire_repository import (
    FireRepositoryInterface,
    SQLAlchemyFireRepository,
    get_fire_repository,
)
from app.repositories.burned_area_repository import (
    BurnedAreaRepositoryInterface,
    SQLAlchemyBurnedAreaRepository,
    get_burned_area_repository,
)
from app.repositories.alert_repository import (
    AlertRepositoryInterface,
    SQLAlchemyAlertRepository,
    get_alert_repository,
)

__all__ = [
    "FireRepositoryInterface",
    "SQLAlchemyFireRepository",
    "get_fire_repository",
    "BurnedAreaRepositoryInterface",
    "SQLAlchemyBurnedAreaRepository",
    "get_burned_area_repository",
    "AlertRepositoryInterface",
    "SQLAlchemyAlertRepository",
    "get_alert_repository",
]
