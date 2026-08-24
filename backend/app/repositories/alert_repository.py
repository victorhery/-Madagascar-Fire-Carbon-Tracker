from abc import ABC, abstractmethod
from typing import List, Optional

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Alert


class AlertRepositoryInterface(ABC):
    @abstractmethod
    def create(self, alert: Alert) -> Alert:
        ...

    @abstractmethod
    def get_by_id(self, alert_id: int) -> Optional[Alert]:
        ...

    @abstractmethod
    def list_active(self) -> List[Alert]:
        """Alertes non résolues (resolved=False) -> alimente le KPI "alertes du jour"."""
        ...

    @abstractmethod
    def list_by_region(self, region: str) -> List[Alert]:
        ...

    @abstractmethod
    def count_active(self) -> int:
        ...


class SQLAlchemyAlertRepository(AlertRepositoryInterface):
    def __init__(self, db: Session):
        self.db = db

    def create(self, alert: Alert) -> Alert:
        self.db.add(alert)
        self.db.commit()
        self.db.refresh(alert)
        return alert

    def get_by_id(self, alert_id: int) -> Optional[Alert]:
        return self.db.get(Alert, alert_id)

    def list_active(self) -> List[Alert]:
        return (
            self.db.query(Alert)
            .filter_by(resolved=False)
            .order_by(Alert.triggered_at.desc())
            .all()
        )

    def list_by_region(self, region: str) -> List[Alert]:
        return (
            self.db.query(Alert)
            .filter_by(region=region)
            .order_by(Alert.triggered_at.desc())
            .all()
        )

    def count_active(self) -> int:
        return self.db.query(Alert).filter_by(resolved=False).count()


def get_alert_repository(db: Session = Depends(get_db)) -> AlertRepositoryInterface:
    return SQLAlchemyAlertRepository(db)
