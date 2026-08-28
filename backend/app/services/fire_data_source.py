import csv
import io
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, datetime
from typing import List, Optional

import httpx

FIRMS_AREA_URL = "https://firms.modaps.eosdis.nasa.gov/api/area/csv"


class FireDataSourceError(Exception):
    pass


@dataclass
class RawFireDetection:
    latitude: float
    longitude: float
    acq_date: date
    acq_time: str
    satellite: str
    brightness: Optional[float] = None
    confidence: Optional[str] = None
    frp: Optional[float] = None


class FireDataSourceInterface(ABC):
    @abstractmethod
    async def fetch_recent(self, day_range: int = 1) -> List[RawFireDetection]: ...


class FirmsFetcherService(FireDataSourceInterface):
    """
    Interroge FIRMS sur un ou plusieurs satellites, et fusionne les résultats.
    Combiner plusieurs satellites (ex: VIIRS + MODIS) réduit les détections
    manquées : un satellite peut voir un feu que l'autre a raté (nuages,
    heure de passage différente).

    Chaque détection reste identifiée par SON satellite d'origine (le champ
    `satellite` de RawFireDetection) -> deux satellites qui voient le même
    feu réel produisent 2 lignes distinctes en base, pas un doublon
    (cohérent avec la UniqueConstraint du modèle, qui inclut le satellite).
    """

    DEFAULT_SATELLITES = ["VIIRS_SNPP_NRT", "MODIS_NRT"]

    def __init__(self, api_key: str, bbox: str, satellites: Optional[List[str]] = None):
        self.api_key = api_key
        self.bbox = bbox
        self.satellites = satellites or list(self.DEFAULT_SATELLITES)

    async def fetch_recent(self, day_range: int = 1) -> List[RawFireDetection]:
        if not self.api_key:
            raise FireDataSourceError("Clé API FIRMS manquante.")

        all_detections: List[RawFireDetection] = []
        errors: List[str] = []

        async with httpx.AsyncClient() as client:
            for satellite in self.satellites:
                url = f"{FIRMS_AREA_URL}/{self.api_key}/{satellite}/{self.bbox}/{day_range}"
                try:
                    response = await client.get(url, timeout=10.0)
                    response.raise_for_status()
                    all_detections.extend(self._parse_csv(response.text, satellite))
                except httpx.HTTPError as exc:
                    # Un satellite en panne ne doit pas faire perdre les
                    # données des autres -> on continue, on trace l'erreur.
                    errors.append(f"{satellite}: {exc}")

        if errors and len(errors) == len(self.satellites):
            raise FireDataSourceError(
                f"Tous les satellites FIRMS ont échoué : {'; '.join(errors)}"
            )

        return all_detections

    def _parse_csv(self, csv_text: str, satellite: str) -> List[RawFireDetection]:
        reader = csv.DictReader(io.StringIO(csv_text))
        detections: List[RawFireDetection] = []
        for row in reader:
            try:
                # VIIRS utilise "bright_ti4", MODIS utilise "brightness" ->
                # sans ce repli, la luminosité des lignes MODIS serait
                # silencieusement vide.
                brightness_raw = row.get("bright_ti4") or row.get("brightness")

                detections.append(RawFireDetection(
                    latitude=float(row["latitude"]),
                    longitude=float(row["longitude"]),
                    acq_date=datetime.strptime(row["acq_date"], "%Y-%m-%d").date(),
                    acq_time=row.get("acq_time", ""),
                    satellite=satellite,
                    brightness=float(brightness_raw) if brightness_raw else None,
                    confidence=row.get("confidence"),
                    frp=float(row["frp"]) if row.get("frp") else None,
                ))
            except (ValueError, KeyError):
                continue
        return detections


def get_firms_fetcher_service() -> FireDataSourceInterface:
    from app.core.config import settings
    return FirmsFetcherService(api_key=settings.NASA_MAP_KEY, bbox=settings.COFAV_BBOX)
