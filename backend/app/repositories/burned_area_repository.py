import datetime
from abc import ABC, abstractmethod
from typing import List, Optional

from fastapi import Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import BurnedArea


class BurnedAreaRepositoryInterface(ABC):
    @abstractmethod
    def create(self, burned_area: BurnedArea) -> BurnedArea:
        ...

    @abstractmethod
    def get_by_id(self, burned_area_id: int) -> Optional[BurnedArea]:
        ...

    @abstractmethod
    def list_by_region(self, region: str) -> List[BurnedArea]:
        ...

    @abstractmethod
    def list_recent(self, since: datetime.date) -> List[BurnedArea]:
        ...

    @abstractmethod
    def totals(self):
        """Retourne (surface totale en hectares, carbone total en tonnes)."""
        ...


class SQLAlchemyBurnedAreaRepository(BurnedAreaRepositoryInterface):
    def __init__(self, db: Session):
        self.db = db

    def create(self, burned_area: BurnedArea) -> BurnedArea:
        self.db.add(burned_area)
        self.db.commit()
        self.db.refresh(burned_area)
        return burned_area

    def get_by_id(self, burned_area_id: int) -> Optional[BurnedArea]:
        return self.db.get(BurnedArea, burned_area_id)

    def list_by_region(self, region: str) -> List[BurnedArea]:
        return (
            self.db.query(BurnedArea)
            .filter_by(region=region)
            .order_by(BurnedArea.computed_at.desc())
            .all()
        )

    def list_recent(self, since: datetime.date) -> List[BurnedArea]:
        return (
            self.db.query(BurnedArea)
            .filter(BurnedArea.period_end >= since)
            .order_by(BurnedArea.computed_at.desc())
            .all()
        )

    def totals(self):
        area_sum, carbon_sum = self.db.query(
            func.coalesce(func.sum(BurnedArea.area_hectares), 0.0),
            func.coalesce(func.sum(BurnedArea.carbon_tons_estimate), 0.0),
        ).one()
        return float(area_sum), float(carbon_sum)


def get_burned_area_repository(
    db: Session = Depends(get_db),
) -> BurnedAreaRepositoryInterface:
    return SQLAlchemyBurnedAreaRepository(db)
