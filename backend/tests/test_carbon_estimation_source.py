import datetime
from unittest.mock import MagicMock

import pytest

from app.services import CarbonEstimationError, GeeCarbonEstimationService


def make_mocked_ee(mocker, area_m2: float, collection_size: int = 1):
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
    mock_filtered_by_bounds.size.return_value.getInfo.return_value = collection_size

    mock_filtered_by_date = MagicMock()
    mock_filtered_by_date.filterBounds.return_value = mock_filtered_by_bounds

    mock_ee = mocker.patch("app.services.carbon_estimation_source.ee")
    mock_ee.ImageCollection.return_value.filterDate.return_value = mock_filtered_by_date
    mock_ee.Initialize.return_value = None
    mock_ee.ServiceAccountCredentials.return_value = MagicMock()

    return mock_ee


# ---------- Mode compte de service (production / ONG) ----------

def test_estimate_burned_area_computes_hectares_and_carbon_with_service_account(mocker):
    make_mocked_ee(mocker, area_m2=420_000)

    service = GeeCarbonEstimationService(
        service_account_json="{\"fake\": \"credentials\"}", carbon_factor_tons_per_hectare=150.0,
    )
    result = service.estimate_burned_area(
        region="Ihorombe", bbox=(46.5, -22.5, 47.8, -20.5),
        period_start=datetime.date(2026, 7, 20), period_end=datetime.date(2026, 7, 27),
    )

    assert result.area_hectares == 42.0
    assert result.carbon_tons_estimate == 42.0 * 150.0


def test_service_account_mode_calls_service_account_credentials(mocker):
    mock_ee = make_mocked_ee(mocker, area_m2=100_000)

    service = GeeCarbonEstimationService(service_account_json="{\"fake\": \"credentials\"}", project_id="madagascar-firecarbon")
    service.estimate_burned_area(
        region="A", bbox=(46.5, -22.5, 47.8, -20.5),
        period_start=datetime.date(2026, 7, 20), period_end=datetime.date(2026, 7, 27),
    )

    mock_ee.ServiceAccountCredentials.assert_called_once()
    mock_ee.Initialize.assert_called_once()


# ---------- Mode authentification personnelle (dev local) ----------

def test_personal_auth_mode_initializes_without_service_account(mocker):
    mock_ee = make_mocked_ee(mocker, area_m2=210_000)

    service = GeeCarbonEstimationService(service_account_json="", project_id="madagascar-firecarbon")
    result = service.estimate_burned_area(
        region="Vatovavy", bbox=(46.5, -22.5, 47.8, -20.5),
        period_start=datetime.date(2026, 7, 20), period_end=datetime.date(2026, 7, 27),
    )

    assert result.area_hectares == 21.0
    mock_ee.ServiceAccountCredentials.assert_not_called()  # pas de compte de service utilisé
    mock_ee.Initialize.assert_called_once_with(project="madagascar-firecarbon")


def test_raises_when_neither_service_account_nor_project_id_configured(mocker):
    service = GeeCarbonEstimationService(service_account_json="", project_id="")

    with pytest.raises(CarbonEstimationError):
        service.estimate_burned_area(
            region="Ihorombe", bbox=(46.5, -22.5, 47.8, -20.5),
            period_start=datetime.date(2026, 7, 20), period_end=datetime.date(2026, 7, 27),
        )


# ---------- Comportements communs aux 2 modes ----------

def test_estimate_burned_area_handles_zero_burned_area(mocker):
    make_mocked_ee(mocker, area_m2=0)

    service = GeeCarbonEstimationService(project_id="madagascar-firecarbon")
    result = service.estimate_burned_area(
        region="Vatovavy", bbox=(46.5, -22.5, 47.8, -20.5),
        period_start=datetime.date(2026, 7, 20), period_end=datetime.date(2026, 7, 27),
    )

    assert result.area_hectares == 0.0
    assert result.carbon_tons_estimate == 0.0


def test_estimate_burned_area_returns_zero_when_no_modis_image_available(mocker):
    """
    Reproduit le bug rencontré en conditions réelles : MCD64A1 est mensuel
    et publié avec délai -> une période récente peut avoir 0 image
    disponible. Doit renvoyer 0, pas planter sur une image à 0 bande.
    """
    mock_ee = make_mocked_ee(mocker, area_m2=0, collection_size=0)

    service = GeeCarbonEstimationService(project_id="madagascar-firecarbon")
    result = service.estimate_burned_area(
        region="COFAV", bbox=(46.5, -22.5, 47.8, -20.5),
        period_start=datetime.date(2026, 8, 10), period_end=datetime.date(2026, 8, 26),
    )

    assert result.area_hectares == 0.0
    assert result.carbon_tons_estimate == 0.0
    mock_ee.ImageCollection.return_value.filterDate.return_value.filterBounds.return_value.select.assert_not_called()


def test_estimate_burned_area_wraps_gee_errors(mocker):
    mock_ee = mocker.patch("app.services.carbon_estimation_source.ee")
    mock_ee.Initialize.side_effect = RuntimeError("projet non enregistré pour Earth Engine")

    service = GeeCarbonEstimationService(project_id="madagascar-firecarbon")

    with pytest.raises(CarbonEstimationError):
        service.estimate_burned_area(
            region="Ihorombe", bbox=(46.5, -22.5, 47.8, -20.5),
            period_start=datetime.date(2026, 7, 20), period_end=datetime.date(2026, 7, 27),
        )


def test_estimate_burned_area_initializes_ee_only_once(mocker):
    make_mocked_ee(mocker, area_m2=100_000)

    service = GeeCarbonEstimationService(project_id="madagascar-firecarbon")
    service.estimate_burned_area(
        region="A", bbox=(46.5, -22.5, 47.8, -20.5),
        period_start=datetime.date(2026, 7, 20), period_end=datetime.date(2026, 7, 27),
    )
    service.estimate_burned_area(
        region="B", bbox=(46.5, -22.5, 47.8, -20.5),
        period_start=datetime.date(2026, 7, 20), period_end=datetime.date(2026, 7, 27),
    )

    assert service._initialized is True
