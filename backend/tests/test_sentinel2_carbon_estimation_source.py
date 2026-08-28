import datetime
from unittest.mock import MagicMock

import pytest

from app.services import CarbonEstimationError, Sentinel2CarbonEstimationService


def make_collection_chain(size: int):
    """Simule la chaîne filterDate->filterBounds->filter->map->[collection]."""
    collection_mock = MagicMock()
    collection_mock.size.return_value.getInfo.return_value = size

    root_mock = MagicMock()
    root_mock.filterDate.return_value.filterBounds.return_value.filter.return_value.map.return_value = (
        collection_mock
    )
    return root_mock, collection_mock


def make_mocked_ee(mocker, pre_size: int = 1, post_size: int = 1, area_m2: float = 0):
    pre_root, pre_collection = make_collection_chain(pre_size)
    post_root, post_collection = make_collection_chain(post_size)

    pre_nbr = MagicMock()
    pre_collection.median.return_value.normalizedDifference.return_value.rename.return_value = pre_nbr

    post_nbr = MagicMock()
    post_collection.median.return_value.normalizedDifference.return_value.rename.return_value = post_nbr

    final_stats = MagicMock()
    final_stats.getInfo.return_value = {"dNBR": area_m2}
    pre_nbr.subtract.return_value.rename.return_value.gt.return_value.multiply.return_value.reduceRegion.return_value = (
        final_stats
    )

    mock_ee = mocker.patch("app.services.sentinel2_carbon_estimation_source.ee")
    mock_ee.ImageCollection.side_effect = [pre_root, post_root]
    mock_ee.Initialize.return_value = None
    mock_ee.ServiceAccountCredentials.return_value = MagicMock()

    return mock_ee, pre_nbr, post_nbr


def test_estimate_burned_area_computes_hectares_from_dnbr(mocker):
    make_mocked_ee(mocker, area_m2=210_000)  # 21 hectares

    service = Sentinel2CarbonEstimationService(
        project_id="madagascar-firecarbon", carbon_factor_tons_per_hectare=150.0
    )
    result = service.estimate_burned_area(
        region="COFAV", bbox=(46.5, -22.5, 47.8, -20.5),
        period_start=datetime.date(2026, 8, 1), period_end=datetime.date(2026, 8, 15),
    )

    assert result.area_hectares == 21.0
    assert result.carbon_tons_estimate == 21.0 * 150.0


def test_estimate_burned_area_returns_zero_when_pre_period_has_no_images(mocker):
    """Composite 'avant' vide (trop nuageux) -> 0 ha, pas une erreur."""
    make_mocked_ee(mocker, pre_size=0, post_size=1)

    service = Sentinel2CarbonEstimationService(project_id="madagascar-firecarbon")
    result = service.estimate_burned_area(
        region="COFAV", bbox=(46.5, -22.5, 47.8, -20.5),
        period_start=datetime.date(2026, 8, 1), period_end=datetime.date(2026, 8, 15),
    )

    assert result.area_hectares == 0.0


def test_estimate_burned_area_returns_zero_when_post_period_has_no_images(mocker):
    make_mocked_ee(mocker, pre_size=1, post_size=0)

    service = Sentinel2CarbonEstimationService(project_id="madagascar-firecarbon")
    result = service.estimate_burned_area(
        region="COFAV", bbox=(46.5, -22.5, 47.8, -20.5),
        period_start=datetime.date(2026, 8, 1), period_end=datetime.date(2026, 8, 15),
    )

    assert result.area_hectares == 0.0


def test_estimate_burned_area_raises_when_no_credentials_configured(mocker):
    service = Sentinel2CarbonEstimationService(project_id="", service_account_json="")

    with pytest.raises(CarbonEstimationError):
        service.estimate_burned_area(
            region="COFAV", bbox=(46.5, -22.5, 47.8, -20.5),
            period_start=datetime.date(2026, 8, 1), period_end=datetime.date(2026, 8, 15),
        )


def test_estimate_burned_area_wraps_gee_errors(mocker):
    mock_ee = mocker.patch("app.services.sentinel2_carbon_estimation_source.ee")
    mock_ee.Initialize.side_effect = RuntimeError("projet non enregistré")

    service = Sentinel2CarbonEstimationService(project_id="madagascar-firecarbon")

    with pytest.raises(CarbonEstimationError):
        service.estimate_burned_area(
            region="COFAV", bbox=(46.5, -22.5, 47.8, -20.5),
            period_start=datetime.date(2026, 8, 1), period_end=datetime.date(2026, 8, 15),
        )


def test_estimate_burned_area_uses_service_account_when_provided(mocker):
    mock_ee, _, _ = make_mocked_ee(mocker, area_m2=100_000)

    service = Sentinel2CarbonEstimationService(
        service_account_json="{\"fake\": \"credentials\"}", project_id="madagascar-firecarbon"
    )
    service.estimate_burned_area(
        region="COFAV", bbox=(46.5, -22.5, 47.8, -20.5),
        period_start=datetime.date(2026, 8, 1), period_end=datetime.date(2026, 8, 15),
    )

    mock_ee.ServiceAccountCredentials.assert_called_once()
