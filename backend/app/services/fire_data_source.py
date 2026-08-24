import csv
import io
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, datetime
from typing import List, Optional

import httpx

FIRMS_AREA_URL = "https://firms.modaps.eosdis.nasa.gov/api/area/csv"


class FireDataSourceError(Exception):
    """
    Erreur levée quand la source de données de feux (FIRMS aujourd'hui,
    potentiellement une autre source demain) est indisponible ou renvoie
    une réponse invalide. Volontairement indépendante de FastAPI/HTTPException
    (principe S : ce module ne connaît que la donnée, pas le web) — c'est
    à l'appelant (route, job) de la traduire en réponse HTTP si besoin.
    """


@dataclass
class RawFireDetection:
    """
    Détection de feu telle que reçue de la source externe, AVANT tout
    passage en base. Volontairement distincte du modèle SQLAlchemy
    FireDetection (principe S : ce module ne connaît rien de PostgreSQL).
    """

    latitude: float
    longitude: float
    acq_date: date
    acq_time: str
    satellite: str
    brightness: Optional[float] = None
    confidence: Optional[str] = None
    frp: Optional[float] = None


class FireDataSourceInterface(ABC):
    """Interface : n'importe quelle source de détections de feux futures
    (autre satellite, autre fournisseur) pourra l'implémenter sans that
    le code appelant (job, tests) n'ait à changer (principe O)."""

    @abstractmethod
    async def fetch_recent(self, day_range: int = 1) -> List[RawFireDetection]:
        ...


class FirmsFetcherService(FireDataSourceInterface):
    """Implémentation concrète pour NASA FIRMS (VIIRS_SNPP_NRT)."""

    def __init__(self, api_key: str, bbox: str, satellite: str = "VIIRS_SNPP_NRT"):
        self.api_key = api_key
        self.bbox = bbox
        self.satellite = satellite

    async def fetch_recent(self, day_range: int = 1) -> List[RawFireDetection]:
        if not self.api_key:
            raise FireDataSourceError("Clé API FIRMS manquante.")

        url = f"{FIRMS_AREA_URL}/{self.api_key}/{self.satellite}/{self.bbox}/{day_range}"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=10.0)
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise FireDataSourceError(f"Erreur réseau FIRMS : {exc}") from exc

        return self._parse_csv(response.text)

    def _parse_csv(self, csv_text: str) -> List[RawFireDetection]:
        reader = csv.DictReader(io.StringIO(csv_text))
        detections: List[RawFireDetection] = []

        for row in reader:
            try:
                detections.append(
                    RawFireDetection(
                        latitude=float(row["latitude"]),
                        longitude=float(row["longitude"]),
                        acq_date=datetime.strptime(row["acq_date"], "%Y-%m-%d").date(),
                        acq_time=row.get("acq_time", ""),
                        satellite=self.satellite,
                        brightness=float(row["bright_ti4"]) if row.get("bright_ti4") else None,
                        confidence=row.get("confidence"),
                        frp=float(row["frp"]) if row.get("frp") else None,
                    )
                )
            except (ValueError, KeyError):
                # Ligne malformée renvoyée par FIRMS -> ignorée, comme dans
                # l'implémentation d'origine dans main.py.
                continue

        return detections


def get_firms_fetcher_service() -> FireDataSourceInterface:
    """
    Factory utilisée par le job de polling (Phase 4) et les futures routes.
    Importé ici plutôt qu'en haut du fichier pour éviter tout couplage
    circulaire entre app.core.config et app.services.
    """
    from app.core.config import settings

    return FirmsFetcherService(api_key=settings.NASA_MAP_KEY, bbox=settings.COFAV_BBOX)
