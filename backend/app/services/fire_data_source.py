import csv
import io
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, datetime
from typing import List, Optional

import httpx


FIRMS_AREA_URL = "https://firms.modaps.eosdis.nasa.gov/api/area/csv"

logger = logging.getLogger("firms")


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
    async def fetch_recent(
        self,
        day_range: int = 1,
    ) -> List[RawFireDetection]:
        ...


class FirmsFetcherService(FireDataSourceInterface):
    """
    Récupère les détections actives VIIRS et MODIS.

    Chaque détection conserve le nom du flux FIRMS dont elle provient.
    Les réponses sont contrôlées avant de lire les lignes CSV.
    """

    DEFAULT_SATELLITES = [
        "VIIRS_SNPP_NRT",
        "VIIRS_NOAA20_NRT",
        "VIIRS_NOAA21_NRT",
        "MODIS_NRT",
    ]

    REQUIRED_COLUMNS = {
        "latitude",
        "longitude",
        "acq_date",
        "acq_time",
    }

    def __init__(
        self,
        api_key: str,
        bbox: str,
        satellites: Optional[List[str]] = None,
    ):
        self.api_key = api_key.strip()
        self.bbox = bbox.strip()
        self.satellites = (
            list(self.DEFAULT_SATELLITES)
            if satellites is None
            else list(satellites)
        )

    def _safe_message(self, message: str) -> str:
        """Évite de recopier la clé API dans nos messages."""
        if self.api_key:
            return message.replace(self.api_key, "[CLE_MASQUEE]")
        return message

    async def fetch_recent(
        self,
        day_range: int = 1,
    ) -> List[RawFireDetection]:
        if not self.api_key:
            raise FireDataSourceError("Clé API FIRMS manquante.")

        if not self.satellites:
            raise FireDataSourceError("Aucune source FIRMS configurée.")

        all_detections: List[RawFireDetection] = []
        errors: List[str] = []

        logger.info(
            "Début de récupération : zone=%s, fenêtre=%s jour(s).",
            self.bbox,
            day_range,
        )

        async with httpx.AsyncClient() as client:
            for satellite in self.satellites:
                url = (
                    f"{FIRMS_AREA_URL}/{self.api_key}/"
                    f"{satellite}/{self.bbox}/{day_range}"
                )

                try:
                    response = await client.get(url, timeout=30.0)
                    response.raise_for_status()

                    detections = self._parse_csv(
                        response.text,
                        satellite,
                    )
                    all_detections.extend(detections)

                    logger.info(
                        "%s : CSV valide, %s détection(s).",
                        satellite,
                        len(detections),
                    )

                except httpx.HTTPStatusError as exc:
                    message = (
                        f"{satellite} : erreur HTTP "
                        f"{exc.response.status_code}."
                    )
                    errors.append(message)
                    logger.warning("%s", message)

                except httpx.RequestError as exc:
                    message = (
                        f"{satellite} : erreur réseau "
                        f"({type(exc).__name__})."
                    )
                    errors.append(message)
                    logger.warning("%s", message)

                except FireDataSourceError as exc:
                    message = self._safe_message(str(exc))
                    errors.append(message)
                    logger.warning("%s", message)

        if len(errors) == len(self.satellites):
            raise FireDataSourceError(
                "Toutes les sources FIRMS ont échoué : "
                + " | ".join(errors)
            )

        if errors:
            logger.warning(
                "Récupération partielle : %s source(s) en erreur sur %s.",
                len(errors),
                len(self.satellites),
            )

        return all_detections

    def _parse_csv(
        self,
        csv_text: str,
        satellite: str,
    ) -> List[RawFireDetection]:
        text = csv_text.lstrip("\ufeff").strip()

        if not text:
            raise FireDataSourceError(
                f"{satellite} : réponse vide, sans en-tête CSV. "
                "Impossible de confirmer l'absence de détections."
            )

        try:
            reader = csv.DictReader(io.StringIO(text))

            # Normalise les noms de colonnes.
            reader.fieldnames = [
                column.strip()
                for column in (reader.fieldnames or [])
            ]

            missing_columns = (
                self.REQUIRED_COLUMNS - set(reader.fieldnames)
            )

            if missing_columns:
                preview = self._safe_message(
                    " ".join(text.split())[:240]
                )
                raise FireDataSourceError(
                    f"{satellite} : réponse non conforme au CSV attendu. "
                    f"Colonnes manquantes : "
                    f"{', '.join(sorted(missing_columns))}. "
                    f"Extrait : {preview}"
                )

            detections: List[RawFireDetection] = []
            invalid_rows = 0

            for row in reader:
                try:
                    brightness_raw = (
                        row.get("bright_ti4")
                        or row.get("brightness")
                    )

                    raw_time = str(
                        row.get("acq_time") or ""
                    ).strip()
                    acquisition_time = raw_time.zfill(4)

                    if (
                        len(acquisition_time) != 4
                        or not acquisition_time.isdigit()
                    ):
                        raise ValueError("Heure FIRMS invalide.")

                    datetime.strptime(acquisition_time, "%H%M")

                    latitude = float(row["latitude"])
                    longitude = float(row["longitude"])

                    if not (
                        -90 <= latitude <= 90
                        and -180 <= longitude <= 180
                    ):
                        raise ValueError("Coordonnées invalides.")

                    detections.append(
                        RawFireDetection(
                            latitude=latitude,
                            longitude=longitude,
                            acq_date=datetime.strptime(
                                row["acq_date"].strip(),
                                "%Y-%m-%d",
                            ).date(),
                            acq_time=acquisition_time,
                            satellite=satellite,
                            brightness=(
                                float(brightness_raw)
                                if brightness_raw
                                else None
                            ),
                            confidence=row.get("confidence"),
                            frp=(
                                float(row["frp"])
                                if row.get("frp")
                                else None
                            ),
                        )
                    )

                except (ValueError, KeyError, TypeError, AttributeError):
                    invalid_rows += 1

        except csv.Error as exc:
            raise FireDataSourceError(
                f"{satellite} : CSV illisible."
            ) from exc

        if invalid_rows:
            logger.warning(
                "%s : %s ligne(s) CSV invalide(s) ignorée(s).",
                satellite,
                invalid_rows,
            )

            if not detections:
                raise FireDataSourceError(
                    f"{satellite} : aucune ligne exploitable parmi "
                    f"{invalid_rows} ligne(s) reçue(s)."
                )

        return detections


def get_firms_fetcher_service() -> FireDataSourceInterface:
    from app.core.config import settings

    return FirmsFetcherService(
        api_key=settings.NASA_MAP_KEY,
        bbox=settings.COFAV_BBOX,
    )