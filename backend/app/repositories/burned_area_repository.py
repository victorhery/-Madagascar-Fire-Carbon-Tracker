import datetime
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple

from fastapi import Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import BurnedArea

PREFERRED_SOURCE = "sentinel2"


def _rank(row: BurnedArea) -> int:
    """1 = Sentinel-2 non-nul, 2 = Sentinel-2 à 0, 3 = MODIS non-nul, 4 = MODIS à 0."""
    is_preferred = row.source == PREFERRED_SOURCE
    is_nonzero = row.area_hectares > 0
    if is_preferred and is_nonzero:
        return 1
    if is_preferred:
        return 2
    if is_nonzero:
        return 3
    return 4


class BurnedAreaRepositoryInterface(ABC):
    @abstractmethod
    def create(self, burned_area: BurnedArea) -> BurnedArea:
        ...

    @abstractmethod
    def get_by_id(self, burned_area_id: int) -> Optional[BurnedArea]:
        ...

    @abstractmethod
    def get_by_natural_key(
        self, region: str, source: str,
        period_start: datetime.date, period_end: datetime.date,
    ) -> Optional[BurnedArea]:
        """Dédoublonnage pour run_estimate_burned_area_daily : un jour déjà
        connu pour cette région+source n'est jamais recréé."""
        ...

    @abstractmethod
    def list_by_region(self, region: str) -> List[BurnedArea]:
        ...

    @abstractmethod
    def list_recent(self, since: datetime.date) -> List[BurnedArea]:
        """Liste BRUTE (tous les runs, y compris les anciens scans par
        fenêtre) -> usage debug/admin."""
        ...

    @abstractmethod
    def list_daily_history(self, since: datetime.date, region: Optional[str] = None) -> List[BurnedArea]:
        """Lignes QUOTIDIENNES uniquement (period_start == period_end),
        triées du plus récent au plus ancien -> alimente le tableau
        historique paginé du dashboard."""
        ...

    @abstractmethod
    def totals(self, since: Optional[datetime.date] = None) -> Tuple[float, float]:
        ...

    @abstractmethod
    def latest_by_region(self) -> List[BurnedArea]:
        ...

    @abstractmethod
    def latest_by_region_and_source(self) -> List[BurnedArea]:
        ...

    @abstractmethod
    def totals_latest_per_region(self) -> Tuple[float, float]:
        ...

    @abstractmethod
    def total_by_day_preferred(self, since: datetime.date) -> Tuple[float, float]:
        ...

    @abstractmethod
    def latest_daily_by_region(self) -> List[BurnedArea]:
        """
        Une ligne par région : le résultat du JOUR LE PLUS RÉCENT détecté,
        basé sur period_start (la date réelle du feu), PAS computed_at (la
        date où le calcul a été lancé). S'il y a un feu aujourd'hui, c'est
        celui-là qui remonte ; sinon, le dernier jour connu reste affiché.
        Même priorité Sentinel-2 > MODIS que latest_by_region, mais
        uniquement sur les lignes quotidiennes (jamais un ancien scan par
        fenêtre). C'est CETTE méthode qui alimente les StatCard du dashboard.
        """
        ...

    @abstractmethod
    def totals_latest_daily_per_region(self) -> Tuple[float, float]:
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

    def get_by_natural_key(
        self, region: str, source: str,
        period_start: datetime.date, period_end: datetime.date,
    ) -> Optional[BurnedArea]:
        return (
            self.db.query(BurnedArea)
            .filter_by(region=region, source=source, period_start=period_start, period_end=period_end)
            .first()
        )

    def list_by_region(self, region: str) -> List[BurnedArea]:
        return (
            self.db.query(BurnedArea)
            .filter_by(region=region)
            .order_by(BurnedArea.computed_at.desc(), BurnedArea.id.desc())
            .all()
        )

    def list_recent(self, since: datetime.date) -> List[BurnedArea]:
        return (
            self.db.query(BurnedArea)
            .filter(BurnedArea.period_end >= since)
            .order_by(BurnedArea.computed_at.desc(), BurnedArea.id.desc())
            .all()
        )

    def list_daily_history(self, since: datetime.date, region: Optional[str] = None) -> List[BurnedArea]:
        query = (
            self.db.query(BurnedArea)
            .filter(BurnedArea.period_start == BurnedArea.period_end)
            .filter(BurnedArea.period_end >= since)
        )
        if region is not None:
            query = query.filter(BurnedArea.region == region)
        return query.order_by(BurnedArea.period_start.desc(), BurnedArea.id.desc()).all()

    def totals(self, since: Optional[datetime.date] = None) -> Tuple[float, float]:
        query = self.db.query(
            func.coalesce(func.sum(BurnedArea.area_hectares), 0.0),
            func.coalesce(func.sum(BurnedArea.carbon_tons_estimate), 0.0),
        )
        if since is not None:
            query = query.filter(BurnedArea.period_end >= since)

        area_sum, carbon_sum = query.one()
        return float(area_sum), float(carbon_sum)

    def _all_rows_newest_first(self) -> List[BurnedArea]:
        return (
            self.db.query(BurnedArea)
            .order_by(BurnedArea.computed_at.desc(), BurnedArea.id.desc())
            .all()
        )

    def latest_by_region(self) -> List[BurnedArea]:
        all_rows = self._all_rows_newest_first()
        best_by_region_and_rank: Dict[str, Dict[int, BurnedArea]] = {}

        for row in all_rows:
            by_rank = best_by_region_and_rank.setdefault(row.region, {})
            rank = _rank(row)
            if rank not in by_rank:
                by_rank[rank] = row

        result = []
        for by_rank in best_by_region_and_rank.values():
            for rank in (1, 2, 3, 4):
                if rank in by_rank:
                    result.append(by_rank[rank])
                    break
        return result

    def latest_by_region_and_source(self) -> List[BurnedArea]:
        all_rows = self._all_rows_newest_first()

        best_nonzero: Dict[Tuple[str, str], BurnedArea] = {}
        best_any: Dict[Tuple[str, str], BurnedArea] = {}

        for row in all_rows:
            key = (row.region, row.source)
            if key not in best_any:
                best_any[key] = row
            if row.area_hectares > 0 and key not in best_nonzero:
                best_nonzero[key] = row

        rows = [best_nonzero.get(key, fallback) for key, fallback in best_any.items()]
        return sorted(rows, key=lambda r: (r.region, 0 if r.source == PREFERRED_SOURCE else 1))

    def totals_latest_per_region(self) -> Tuple[float, float]:
        rows = self.latest_by_region()
        area_total = sum(row.area_hectares for row in rows)
        carbon_total = sum(row.carbon_tons_estimate for row in rows)
        return float(area_total), float(carbon_total)

    def total_by_day_preferred(self, since: datetime.date) -> Tuple[float, float]:
        daily_rows = self.list_daily_history(since=since)

        best_per_day: Dict[Tuple[str, datetime.date], BurnedArea] = {}
        for row in daily_rows:
            key = (row.region, row.period_start)
            current = best_per_day.get(key)
            if current is None or (row.source == PREFERRED_SOURCE and current.source != PREFERRED_SOURCE):
                best_per_day[key] = row

        area_total = sum(r.area_hectares for r in best_per_day.values())
        carbon_total = sum(r.carbon_tons_estimate for r in best_per_day.values())
        return float(area_total), float(carbon_total)

    def latest_daily_by_region(self) -> List[BurnedArea]:
        daily_rows = (
            self.db.query(BurnedArea)
            .filter(BurnedArea.period_start == BurnedArea.period_end)
            .order_by(BurnedArea.period_start.desc(), BurnedArea.id.desc())
            .all()
        )

        best_by_region_and_rank: Dict[str, Dict[int, BurnedArea]] = {}
        for row in daily_rows:
            by_rank = best_by_region_and_rank.setdefault(row.region, {})
            rank = _rank(row)
            if rank not in by_rank:
                by_rank[rank] = row

        result = []
        for by_rank in best_by_region_and_rank.values():
            for rank in (1, 2, 3, 4):
                if rank in by_rank:
                    result.append(by_rank[rank])
                    break
        return result

    def totals_latest_daily_per_region(self) -> Tuple[float, float]:
        rows = self.latest_daily_by_region()
        area_total = sum(row.area_hectares for row in rows)
        carbon_total = sum(row.carbon_tons_estimate for row in rows)
        return float(area_total), float(carbon_total)


def get_burned_area_repository(
    db: Session = Depends(get_db),
) -> BurnedAreaRepositoryInterface:
    return SQLAlchemyBurnedAreaRepository(db)
