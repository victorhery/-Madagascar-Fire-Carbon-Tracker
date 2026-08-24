import datetime
from unittest.mock import MagicMock

import pytest

from app.services import CarbonEstimationError, GeeCarbonEstimationService


def make_mocked_ee(mocker, area_m2: float):
    """
    Simule toute la chaîne d'appels ee.* utilisée par _compute_burned_area_hectares,
    jusqu'à .getInfo() qui renvoie la surface brûlée en m².
    """
    mock_stats = MagicMock()
    mock_stats.get.return_value.getInfo.return_value = area_m2

    mock_area_image = MagicMock()
    mock_area_image.reduceRegion.return_value = mock_stats

    mock_burned_mask = MagicMock()
    mock_burned_mask.multiply.return_value = mock_area_image

    mock_max_image = MagicMock()
    mock_max_image.gt.return_value = mock_burned_mask

    mock_selected = MagicMock()
    mock_selected.max.return_value = mock_max_image

    mock_filtered_by_bounds = MagicMock()
    mock_filtered_by_bounds.select.return_value = mock_selected

    mock_filtered_by_date = MagicMock()
    mock_filtered_by_date.filterBounds.return_value = mock_filtered_by_bounds

    mock_ee = mocker.patch("app.services.carbon_estimation_source.ee")
    mock_ee.ImageCollection.return_value.filterDate.return_value = mock_filtered_by_date
    mock_ee.Initialize.return_value = None
    mock_ee.ServiceAccountCredentials.return_value = MagicMock()

    return mock_ee


def test_estimate_burned_area_computes_hectares_and_carbon(mocker):
    make_mocked_ee(mocker, area_m2=420_000)  # 420 000 m² = 42 hectares

    service = GeeCarbonEstimationService(
        service_account_json="{\"fake\": \"credentials\"}",
        carbon_factor_tons_per_hectare=150.0,
    )

    result = service.estimate_burned_area(
        region="Ihorombe",
        bbox=(46.5, -22.5, 47.8, -20.5),
        period_start=datetime.date(2026, 7, 20),
        period_end=datetime.date(2026, 7, 27),
    )

    assert result.region == "Ihorombe"
    assert result.area_hectares == 42.0
    assert result.carbon_tons_estimate == 42.0 * 150.0
    assert result.period_start == datetime.date(2026, 7, 20)


def test_estimate_burned_area_handles_zero_burned_area(mocker):
    make_mocked_ee(mocker, area_m2=0)

    service = GeeCarbonEstimationService(service_account_json="{\"fake\": \"credentials\"}")
    result = service.estimate_burned_area(
        region="Vatovavy",
        bbox=(46.5, -22.5, 47.8, -20.5),
        period_start=datetime.date(2026, 7, 20),
        period_end=datetime.date(2026, 7, 27),
    )

    assert result.area_hectares == 0.0
    assert result.carbon_tons_estimate == 0.0


def test_estimate_burned_area_raises_when_credentials_missing(mocker):
    service = GeeCarbonEstimationService(service_account_json="")

    with pytest.raises(CarbonEstimationError):
        service.estimate_burned_area(
            region="Ihorombe",
            bbox=(46.5, -22.5, 47.8, -20.5),
            period_start=datetime.date(2026, 7, 20),
            period_end=datetime.date(2026, 7, 27),
        )


def test_estimate_burned_area_wraps_gee_errors(mocker):
    mock_ee = mocker.patch("app.services.carbon_estimation_source.ee")
    mock_ee.ServiceAccountCredentials.side_effect = RuntimeError("identifiants invalides")

    service = GeeCarbonEstimationService(service_account_json="{\"fake\": \"credentials\"}")

    with pytest.raises(CarbonEstimationError):
        service.estimate_burned_area(
            region="Ihorombe",
            bbox=(46.5, -22.5, 47.8, -20.5),
            period_start=datetime.date(2026, 7, 20),
            period_end=datetime.date(2026, 7, 27),
        )


def test_estimate_burned_area_initializes_ee_only_once(mocker):
    make_mocked_ee(mocker, area_m2=100_000)

    service = GeeCarbonEstimationService(service_account_json="{\"fake\": \"credentials\"}")
    service.estimate_burned_area(
        region="A", bbox=(46.5, -22.5, 47.8, -20.5),
        period_start=datetime.date(2026, 7, 20), period_end=datetime.date(2026, 7, 27),
    )
    service.estimate_burned_area(
        region="B", bbox=(46.5, -22.5, 47.8, -20.5),
        period_start=datetime.date(2026, 7, 20), period_end=datetime.date(2026, 7, 27),
    )

    assert service._initialized is True
