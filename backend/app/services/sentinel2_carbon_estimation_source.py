from datetime import date, timedelta
from typing import Dict, List, Tuple

import ee

from app.services.carbon_estimation_source import (
    CarbonEstimationError,
    CarbonEstimationSourceInterface,
    RawBurnedAreaEstimate,
)


class Sentinel2CarbonEstimationService(CarbonEstimationSourceInterface):
    """
    Implémentation alternative à GeeCarbonEstimationService (MODIS MCD64A1).
    Utilise Sentinel-2 (10-20m de résolution, imagerie disponible en
    quelques jours) plutôt que MODIS (500m, ~2-3 mois de délai).

    Méthode agrégée (estimate_burned_area) : dNBR entre une composite
    "avant" et une composite "après" -> UN blob pour toute la fenêtre.

    Méthode quotidienne (estimate_burned_area_daily) : au lieu d'une seule
    comparaison avant/après, compare CHAQUE passage Sentinel-2 successif au
    passage (ou à la composite pré-feu) précédent -> attribue la surface
    nouvellement brûlée à la date exacte du passage qui l'a révélée. La
    référence "glisse" à chaque image : un pixel déjà détecté brûlé au
    passage N ne réapparaît pas comme "nouveau" au passage N+1.

    ⚠️ Contrepartie du gain de résolution/fraîcheur : contrairement à
    MCD64A1 (produit validé scientifiquement par la NASA), c'est une
    classification maison, avec un seuil approximatif -- traiter le
    résultat comme une estimation indicative, pas une donnée certifiée,
    tant que le seuil n'a pas été calibré sur des feux connus du COFAV.
    """

    SENTINEL2_COLLECTION = "COPERNICUS/S2_SR_HARMONIZED"
    CLOUD_COVER_MAX_PERCENT = 40
    DNBR_BURNED_THRESHOLD = 0.27
    PRE_FIRE_LOOKBACK_DAYS = 60

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
                "Aucune configuration GEE trouvée pour Sentinel-2 "
                "(GEE_SERVICE_ACCOUNT_JSON ou GEE_PROJECT_ID)."
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
            raise CarbonEstimationError(f"Erreur Sentinel-2/GEE : {exc}") from exc

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
                f"Erreur Sentinel-2/GEE (extraction quotidienne) : {exc}"
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

    def _mask_clouds(self, image):
        qa = image.select("QA60")
        cloud_bit = 1 << 10
        cirrus_bit = 1 << 11
        mask = qa.bitwiseAnd(cloud_bit).eq(0).And(qa.bitwiseAnd(cirrus_bit).eq(0))
        return image.updateMask(mask)

    def _nbr_composite(self, geometry, start: date, end: date):
        collection = (
            ee.ImageCollection(self.SENTINEL2_COLLECTION)
            .filterDate(start.isoformat(), end.isoformat())
            .filterBounds(geometry)
            .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", self.CLOUD_COVER_MAX_PERCENT))
            .map(self._mask_clouds)
        )
        composite = collection.median()
        nbr = composite.normalizedDifference(["B8", "B12"]).rename("NBR")
        return collection, nbr

    def _compute_burned_area_hectares(
        self,
        bbox: Tuple[float, float, float, float],
        period_start: date,
        period_end: date,
    ) -> float:
        west, south, east, north = bbox
        geometry = ee.Geometry.Rectangle([west, south, east, north])

        pre_start = period_start - timedelta(days=self.PRE_FIRE_LOOKBACK_DAYS)
        pre_end = period_start

        pre_collection, pre_nbr = self._nbr_composite(geometry, pre_start, pre_end)
        post_collection, post_nbr = self._nbr_composite(geometry, period_start, period_end)

        if pre_collection.size().getInfo() == 0 or post_collection.size().getInfo() == 0:
            return 0.0

        dnbr = pre_nbr.subtract(post_nbr).rename("dNBR")
        burned_mask = dnbr.gt(self.DNBR_BURNED_THRESHOLD)
        area_image = burned_mask.multiply(ee.Image.pixelArea())

        stats = area_image.reduceRegion(
            reducer=ee.Reducer.sum(),
            geometry=geometry,
            scale=20,
            maxPixels=1e9,
        )

        stats_dict = stats.getInfo()
        area_m2 = next(iter(stats_dict.values()), 0) or 0
        return area_m2 / 10000

    def _compute_daily_burned_area_hectares(
        self,
        bbox: Tuple[float, float, float, float],
        period_start: date,
        period_end: date,
    ) -> List[Tuple[date, float]]:
        west, south, east, north = bbox
        geometry = ee.Geometry.Rectangle([west, south, east, north])

        pre_start = period_start - timedelta(days=self.PRE_FIRE_LOOKBACK_DAYS)
        pre_collection, reference_nbr = self._nbr_composite(geometry, pre_start, period_start)

        if pre_collection.size().getInfo() == 0:
            # Pas de composite "avant" -> aucune référence pour détecter un
            # changement, cas normal (zone trop nuageuse récemment).
            return []

        post_collection = (
            ee.ImageCollection(self.SENTINEL2_COLLECTION)
            .filterDate(period_start.isoformat(), period_end.isoformat())
            .filterBounds(geometry)
            .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", self.CLOUD_COVER_MAX_PERCENT))
            .map(self._mask_clouds)
            .sort("system:time_start")
        )

        if post_collection.size().getInfo() == 0:
            return []

        image_list = post_collection.toList(post_collection.size())
        count = image_list.size().getInfo()

        daily_area_m2: Dict[date, float] = {}

        for i in range(count):
            image = ee.Image(image_list.get(i))
            acq_date_str = ee.Date(image.get("system:time_start")).format("YYYY-MM-dd").getInfo()
            image_nbr = image.normalizedDifference(["B8", "B12"]).rename("NBR")

            dnbr = reference_nbr.subtract(image_nbr).rename("dNBR")
            burned_mask = dnbr.gt(self.DNBR_BURNED_THRESHOLD)
            area_image = burned_mask.multiply(ee.Image.pixelArea())

            stats = area_image.reduceRegion(
                reducer=ee.Reducer.sum(), geometry=geometry, scale=20, maxPixels=1e9,
            )
            stats_dict = stats.getInfo()
            area_m2 = next(iter(stats_dict.values()), 0) or 0

            if area_m2 > 0:
                burn_date = date.fromisoformat(acq_date_str)
                daily_area_m2[burn_date] = daily_area_m2.get(burn_date, 0.0) + area_m2

            # La référence glisse : le passage suivant est comparé à
            # CELUI-CI, pas au composite pré-feu d'origine -> une zone déjà
            # détectée brûlée ne réapparaît pas comme "nouvelle" ensuite.
            reference_nbr = image_nbr

        return sorted((day, area_m2 / 10000) for day, area_m2 in daily_area_m2.items())


def get_sentinel2_carbon_estimation_service() -> CarbonEstimationSourceInterface:
    from app.core.config import settings

    return Sentinel2CarbonEstimationService(
        service_account_json=settings.GEE_SERVICE_ACCOUNT_JSON,
        project_id=settings.GEE_PROJECT_ID,
    )
