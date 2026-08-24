import datetime
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from app.services import FireDataSourceError, FirmsFetcherService


def make_mock_client(mocker, response_text: str = "", status_error: bool = False):
    """Construit un httpx.AsyncClient simulé, injecté à la place du vrai."""
    mock_response = MagicMock()
    mock_response.text = response_text

    if status_error:
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "erreur simulée", request=MagicMock(), response=MagicMock()
        )
    else:
        mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    mocker.patch(
        "app.services.fire_data_source.httpx.AsyncClient",
        return_value=mock_client,
    )
    return mock_client


@pytest.mark.asyncio
async def test_fetch_recent_parses_valid_csv(mocker):
    csv_content = (
        "latitude,longitude,bright_ti4,confidence,acq_date,acq_time,frp\n"
        "-21.45,47.08,310.5,high,2026-08-01,1415,12.3\n"
    )
    make_mock_client(mocker, response_text=csv_content)

    service = FirmsFetcherService(api_key="fake_key", bbox="46.5,-22.5,47.8,-20.5")
    results = await service.fetch_recent(day_range=1)

    assert len(results) == 1
    fire = results[0]
    assert fire.latitude == -21.45
    assert fire.longitude == 47.08
    assert fire.acq_date == datetime.date(2026, 8, 1)
    assert fire.acq_time == "1415"
    assert fire.satellite == "VIIRS_SNPP_NRT"
    assert fire.confidence == "high"
    assert fire.frp == 12.3


@pytest.mark.asyncio
async def test_fetch_recent_skips_malformed_rows(mocker):
    """Une ligne avec une latitude invalide doit être ignorée, pas planter tout le lot."""
    csv_content = (
        "latitude,longitude,bright_ti4,confidence,acq_date,acq_time,frp\n"
        "-21.45,47.08,310.5,high,2026-08-01,1415,12.3\n"
        "PAS_UN_NOMBRE,47.09,300.0,low,2026-08-01,1420,8.1\n"
    )
    make_mock_client(mocker, response_text=csv_content)

    service = FirmsFetcherService(api_key="fake_key", bbox="46.5,-22.5,47.8,-20.5")
    results = await service.fetch_recent(day_range=1)

    assert len(results) == 1  # la ligne malformée est ignorée


@pytest.mark.asyncio
async def test_fetch_recent_empty_csv_returns_empty_list(mocker):
    make_mock_client(mocker, response_text="latitude,longitude,acq_date,acq_time\n")

    service = FirmsFetcherService(api_key="fake_key", bbox="46.5,-22.5,47.8,-20.5")
    results = await service.fetch_recent(day_range=1)

    assert results == []


@pytest.mark.asyncio
async def test_fetch_recent_raises_domain_error_on_http_failure(mocker):
    """Une erreur réseau/HTTP doit devenir une FireDataSourceError, pas fuiter httpx tel quel."""
    make_mock_client(mocker, status_error=True)

    service = FirmsFetcherService(api_key="fake_key", bbox="46.5,-22.5,47.8,-20.5")

    with pytest.raises(FireDataSourceError):
        await service.fetch_recent(day_range=1)


@pytest.mark.asyncio
async def test_fetch_recent_raises_domain_error_when_api_key_missing(mocker):
    service = FirmsFetcherService(api_key="", bbox="46.5,-22.5,47.8,-20.5")

    with pytest.raises(FireDataSourceError):
        await service.fetch_recent(day_range=1)
