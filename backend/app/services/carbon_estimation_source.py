from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from typing import Tuple

import ee


class CarbonEstimationError(Exception):
    """
    Erreur levée quand la source d'estimation carbone (GEE) est indisponible,
    mal configurée, ou renvoie une réponse invalide. Volontairement
    indépendante de FastAPI (principe S).
    """


@dataclass
class RawBurnedAreaEstimate:
    region: str
    area_hectares: float
    carbon_tons_estimate: float
    period_start: date
    period_end: date


class CarbonEstimationSourceInterface(ABC):
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
    MODIS MCD64A1 (surface brûlée mensuelle, résolution 500m).

    Supporte 2 modes d'authentification, choisis automatiquement :
    1. Compte de service (service_account_json fourni) -> mode prévu pour
       la production/ONG, ne nécessite aucune interaction humaine.
    2. Authentification personnelle (project_id fourni, pas de JSON) ->
       mode dev local, suppose que `earthengine authenticate` a déjà été
       lancé une fois en CLI dans ce venv (credentials mis en cache
       localement par le SDK Earth Engine).

    Le passage du mode 2 au mode 1 (migration vers l'ONG) ne nécessite
    aucun changement de code, juste renseigner GEE_SERVICE_ACCOUNT_JSON
    dans .env à la place de GEE_PROJECT_ID.
    """

    MODIS_BURNED_AREA_COLLECTION = "MODIS/061/MCD64A1"

    def __init__(
        self,
        service_account_json: str = "",
        project_id: str = "",
        carbon_factor_tons_per_hectare: float = 150.0,
    ):
        self.service_account_json = service_account_json
        self.project_id = project_id
        self.carbon_factor_tons_per_hectare = carbon_factor_tons_per_hectare
        self._initialized = False

    def _ensure_initialized(self) -> None:
        if self._initialized:
            return

        if self.service_account_json:
            credentials = ee.ServiceAccountCredentials(
                email=None, key_data=self.service_account_json
            )
            ee.Initialize(credentials, project=self.project_id or None)
        else:
            # Authentification personnelle : les credentials mis en cache
            # localement par `earthengine authenticate` sont utilisés
            # automatiquement, sans navigateur ni prompt supplémentaire.
            ee.Initialize(project=self.project_id)

        self._initialized = True

    def estimate_burned_area(
        self,
        region: str,
        bbox: Tuple[float, float, float, float],
        period_start: date,
        period_end: date,
    ) -> RawBurnedAreaEstimate:
        if not self.service_account_json and not self.project_id:
            raise CarbonEstimationError(
                "Aucune configuration GEE trouvée : renseigne soit "
                "GEE_SERVICE_ACCOUNT_JSON (compte de service), soit "
                "GEE_PROJECT_ID (authentification personnelle) dans .env."
            )

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

        # MCD64A1 est un produit MENSUEL, publié avec plusieurs semaines de
        # délai. Une période récente peut ne contenir AUCUNE image (pas
        # encore publiée) -> cas normal, pas une erreur. Sans cette
        # vérification, .max() sur une collection vide renvoie une image à
        # 0 bande, et .gt() plante juste après.
        if collection.size().getInfo() == 0:
            return 0.0

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
    """Factory utilisée par le job d'estimation et les futures routes."""
    from app.core.config import settings

    return GeeCarbonEstimationService(
        service_account_json=settings.GEE_SERVICE_ACCOUNT_JSON,
        project_id=settings.GEE_PROJECT_ID,
    )
