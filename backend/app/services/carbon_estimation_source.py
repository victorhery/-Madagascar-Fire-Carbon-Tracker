from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from typing import Tuple

import ee


class CarbonEstimationError(Exception):
    """
    Erreur levée quand la source d'estimation carbone (GEE aujourd'hui) est
    indisponible, mal configurée, ou renvoie une réponse invalide.
    Volontairement indépendante de FastAPI (principe S), comme
    FireDataSourceError pour le service FIRMS.
    """


@dataclass
class RawBurnedAreaEstimate:
    """
    Résultat d'estimation tel que reçu de la source externe, AVANT tout
    passage en base. Distinct du modèle SQLAlchemy BurnedArea (principe S).
    """

    region: str
    area_hectares: float
    carbon_tons_estimate: float
    period_start: date
    period_end: date


class CarbonEstimationSourceInterface(ABC):
    """Interface : une autre source d'estimation (autre produit satellite,
    autre méthode de calcul carbone) pourra l'implémenter sans que le code
    appelant n'ait à changer (principe O)."""

    @abstractmethod
    def estimate_burned_area(
        self,
        region: str,
        bbox: Tuple[float, float, float, float],
        period_start: date,
        period_end: date,
    ) -> RawBurnedAreaEstimate:
        ...


class GeeCarbonEstimationService(CarbonEstimationSourceInterface):
    """
    Implémentation concrète utilisant Google Earth Engine et le produit
    MODIS MCD64A1 (surface brûlée mensuelle, résolution 500m) -- un jeu de
    données standard et déjà validé scientifiquement, plutôt qu'une
    classification NDVI/dNBR maison qui demanderait un calibrage propre à
    la zone COFAV.

    Le facteur carbone (tonnes de carbone par hectare brûlé) est une
    approximation générique pour forêt humide malgache -- à affiner plus
    tard avec des coefficients IPCC Tier 2 propres à la végétation locale
    si une précision scientifique plus fine est nécessaire.
    """

    MODIS_BURNED_AREA_COLLECTION = "MODIS/061/MCD64A1"

    def __init__(
        self,
        service_account_json: str,
        carbon_factor_tons_per_hectare: float = 150.0,
    ):
        self.service_account_json = service_account_json
        self.carbon_factor_tons_per_hectare = carbon_factor_tons_per_hectare
        self._initialized = False

    def _ensure_initialized(self) -> None:
        if self._initialized:
            return
        credentials = ee.ServiceAccountCredentials(
            email=None, key_data=self.service_account_json
        )
        ee.Initialize(credentials)
        self._initialized = True

    def estimate_burned_area(
        self,
        region: str,
        bbox: Tuple[float, float, float, float],
        period_start: date,
        period_end: date,
    ) -> RawBurnedAreaEstimate:
        if not self.service_account_json:
            raise CarbonEstimationError("Clé de service GEE manquante (GEE_SERVICE_ACCOUNT_JSON).")

        try:
            self._ensure_initialized()
            area_hectares = self._compute_burned_area_hectares(bbox, period_start, period_end)
        except CarbonEstimationError:
            raise
        except Exception as exc:
            raise CarbonEstimationError(f"Erreur Google Earth Engine : {exc}") from exc

        carbon_tons = area_hectares * self.carbon_factor_tons_per_hectare

        return RawBurnedAreaEstimate(
            region=region,
            area_hectares=area_hectares,
            carbon_tons_estimate=carbon_tons,
            period_start=period_start,
            period_end=period_end,
        )

    def _compute_burned_area_hectares(
        self,
        bbox: Tuple[float, float, float, float],
        period_start: date,
        period_end: date,
    ) -> float:
        west, south, east, north = bbox
        geometry = ee.Geometry.Rectangle([west, south, east, north])

        collection = (
            ee.ImageCollection(self.MODIS_BURNED_AREA_COLLECTION)
            .filterDate(period_start.isoformat(), period_end.isoformat())
            .filterBounds(geometry)
        )

        burned_mask = collection.select("BurnDate").max().gt(0)
        area_image = burned_mask.multiply(ee.Image.pixelArea())

        stats = area_image.reduceRegion(
            reducer=ee.Reducer.sum(),
            geometry=geometry,
            scale=500,
            maxPixels=1e9,
        )

        area_m2 = stats.get("BurnDate").getInfo() or 0
        return area_m2 / 10000  # m² -> hectares


def get_gee_carbon_estimation_service() -> CarbonEstimationSourceInterface:
    """Factory utilisée par le futur job d'estimation et les futures routes."""
    from app.core.config import settings

    return GeeCarbonEstimationService(service_account_json=settings.GEE_SERVICE_ACCOUNT_JSON)
