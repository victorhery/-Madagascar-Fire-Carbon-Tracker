from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Dict, List, Tuple

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
        """Un seul résultat agrégé pour toute la fenêtre -> utile pour un
        test manuel rapide, mais masque QUAND dans la fenêtre le feu a eu
        lieu. Voir estimate_burned_area_daily pour la version exploitée
        automatiquement par le scheduler."""
        ...

    @abstractmethod
    def estimate_burned_area_daily(
        self,
        region: str,
        bbox: Tuple[float, float, float, float],
        period_start: date,
        period_end: date,
    ) -> List[RawBurnedAreaEstimate]:
        """Une estimation PAR JOUR où une combustion a été détectée dans la
        fenêtre (period_start == period_end sur chaque résultat), au lieu
        d'un seul blob agrégé -> permet de garder un historique jour par
        jour, sans jamais écraser un jour déjà connu."""
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
            ee.Initialize(project=self.project_id)

        self._initialized = True

    def _check_credentials(self) -> None:
        if not self.service_account_json and not self.project_id:
            raise CarbonEstimationError(
                "Aucune configuration GEE trouvée : renseigne soit "
                "GEE_SERVICE_ACCOUNT_JSON (compte de service), soit "
                "GEE_PROJECT_ID (authentification personnelle) dans .env."
            )

    def estimate_burned_area(
        self,
        region: str,
        bbox: Tuple[float, float, float, float],
        period_start: date,
        period_end: date,
    ) -> RawBurnedAreaEstimate:
        self._check_credentials()

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

    def estimate_burned_area_daily(
        self,
        region: str,
        bbox: Tuple[float, float, float, float],
        period_start: date,
        period_end: date,
    ) -> List[RawBurnedAreaEstimate]:
        self._check_credentials()

        try:
            self._ensure_initialized()
            daily_areas = self._compute_daily_burned_area_hectares(bbox, period_start, period_end)
        except CarbonEstimationError:
            raise
        except Exception as exc:
            raise CarbonEstimationError(
                f"Erreur Google Earth Engine (extraction quotidienne) : {exc}"
            ) from exc

        return [
            RawBurnedAreaEstimate(
                region=region,
                area_hectares=area_ha,
                carbon_tons_estimate=area_ha * self.carbon_factor_tons_per_hectare,
                period_start=day,
                period_end=day,
            )
            for day, area_ha in daily_areas
        ]

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
        return area_m2 / 10000

    def _compute_daily_burned_area_hectares(
        self,
        bbox: Tuple[float, float, float, float],
        period_start: date,
        period_end: date,
    ) -> List[Tuple[date, float]]:
        """
        MCD64A1 encode, PAR PIXEL, le jour-de-l'année (1-366) où ce pixel a
        brûlé (bande "BurnDate", 0 = non brûlé). Contrairement à
        _compute_burned_area_hectares (qui fait juste BurnDate > 0 et jette
        cette info), on regroupe ici les pixels par valeur de BurnDate pour
        reconstruire une vraie surface brûlée PAR JOUR.

        1 image MCD64A1 = 1 mois -> on combine l'année de chaque image
        (system:time_start) avec le jour-de-l'année du pixel pour obtenir
        une date calendaire absolue.
        """
        west, south, east, north = bbox
        geometry = ee.Geometry.Rectangle([west, south, east, north])

        collection = (
            ee.ImageCollection(self.MODIS_BURNED_AREA_COLLECTION)
            .filterDate(period_start.isoformat(), period_end.isoformat())
            .filterBounds(geometry)
        )

        if collection.size().getInfo() == 0:
            return []

        image_list = collection.toList(collection.size())
        count = image_list.size().getInfo()

        daily_area_m2: Dict[date, float] = {}

        for i in range(count):
            image = ee.Image(image_list.get(i))
            year = ee.Date(image.get("system:time_start")).get("year").getInfo()

            burn_date_band = image.select("BurnDate")
            combined = ee.Image.pixelArea().addBands(burn_date_band)

            grouped = combined.reduceRegion(
                reducer=ee.Reducer.sum().group(groupField=1, groupName="burn_doy"),
                geometry=geometry,
                scale=500,
                maxPixels=1e9,
            )
            groups = grouped.get("groups").getInfo() or []

            for group in groups:
                doy = int(group.get("burn_doy", 0))
                if doy <= 0:
                    continue  # 0 = pixel non brûlé, exclu du regroupement
                area_m2 = group.get("sum", 0) or 0
                if area_m2 <= 0:
                    continue
                burn_date = date(int(year), 1, 1) + timedelta(days=doy - 1)
                daily_area_m2[burn_date] = daily_area_m2.get(burn_date, 0.0) + area_m2

        return sorted((day, area_m2 / 10000) for day, area_m2 in daily_area_m2.items())


def get_gee_carbon_estimation_service() -> CarbonEstimationSourceInterface:
    """Factory utilisée par le job d'estimation et les futures routes."""
    from app.core.config import settings

    return GeeCarbonEstimationService(
        service_account_json=settings.GEE_SERVICE_ACCOUNT_JSON,
        project_id=settings.GEE_PROJECT_ID,
    )
