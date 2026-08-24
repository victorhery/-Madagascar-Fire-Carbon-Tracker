import datetime
from abc import ABC, abstractmethod
from typing import List, Optional

from fastapi import Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import FireDetection


class FireRepositoryInterface(ABC):
    """
    Interface (principe I de SOLID : ce repository ne connaît que
    FireDetection, jamais BurnedArea ni Alert). Les services et routes
    dépendront de cette abstraction, jamais de SQLAlchemyFireRepository
    directement (principe D).
    """

    @abstractmethod
    def create(self, fire: FireDetection) -> FireDetection:
        ...

    @abstractmethod
    def get_by_id(self, fire_id: int) -> Optional[FireDetection]:
        ...

    @abstractmethod
    def get_by_natural_key(
        self,
        latitude: float,
        longitude: float,
        acq_date: datetime.date,
        acq_time: str,
        satellite: str,
    ) -> Optional[FireDetection]:
        """
        Retrouve une détection par sa clé de dédoublonnage (identique à la
        UniqueConstraint du modèle). Utile pour le job de polling (Phase 4) :
        vérifier AVANT d'insérer, plutôt que de laisser échouer un commit.
        """
        ...

    @abstractmethod
    def list_recent(self, since: datetime.date) -> List[FireDetection]:
        ...

    @abstractmethod
    def count_since(self, since: datetime.date) -> int:
        """Nombre de détections depuis une date -> KPI "feux actifs"."""
        ...

    @abstractmethod
    def count_grouped_by_day(self, since: datetime.date) -> dict:
        """Nombre de détections par jour depuis une date -> trend 7 jours."""
        ...


class SQLAlchemyFireRepository(FireRepositoryInterface):
    """Implémentation concrète, substituable à une autre implémentation
    (principe L) sans jamais casser le code qui dépend de l'interface."""

    def __init__(self, db: Session):
        self.db = db

    def create(self, fire: FireDetection) -> FireDetection:
        self.db.add(fire)
        self.db.commit()
        self.db.refresh(fire)
        return fire

    def get_by_id(self, fire_id: int) -> Optional[FireDetection]:
        return self.db.get(FireDetection, fire_id)

    def get_by_natural_key(
        self,
        latitude: float,
        longitude: float,
        acq_date: datetime.date,
        acq_time: str,
        satellite: str,
    ) -> Optional[FireDetection]:
        return (
            self.db.query(FireDetection)
            .filter_by(
                latitude=latitude,
                longitude=longitude,
                acq_date=acq_date,
                acq_time=acq_time,
                satellite=satellite,
            )
            .first()
        )

    def list_recent(self, since: datetime.date) -> List[FireDetection]:
        return (
            self.db.query(FireDetection)
            .filter(FireDetection.acq_date >= since)
            .order_by(FireDetection.acq_date.desc(), FireDetection.acq_time.desc())
            .all()
        )

    def count_since(self, since: datetime.date) -> int:
        return self.db.query(FireDetection).filter(FireDetection.acq_date >= since).count()

    def count_grouped_by_day(self, since: datetime.date) -> dict:
        rows = (
            self.db.query(FireDetection.acq_date, func.count(FireDetection.id))
            .filter(FireDetection.acq_date >= since)
            .group_by(FireDetection.acq_date)
            .all()
        )
        return {row[0]: row[1] for row in rows}


def get_fire_repository(db: Session = Depends(get_db)) -> FireRepositoryInterface:
    """
    Factory pour l'injection de dépendance FastAPI.
    Les futures routes utiliseront : repo: FireRepositoryInterface = Depends(get_fire_repository)
    """
    return SQLAlchemyFireRepository(db)
