import datetime
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from app.services import FireDataSourceError, FirmsFetcherService

VIIRS_CSV = (
    "latitude,longitude,bright_ti4,confidence,acq_date,acq_time,frp\n"
    "-21.45,47.08,310.5,high,2026-08-01,1415,12.3\n"
)
MODIS_CSV = (
    "latitude,longitude,brightness,confidence,acq_date,acq_time,frp\n"
    "-21.50,47.10,330.2,80,2026-08-01,1420,15.1\n"
)


def make_mock_client(mocker, responses_by_satellite: dict):
    mock_client = AsyncMock()

    async def fake_get(url, timeout=10.0):
        satellite = next(sat for sat in responses_by_satellite if sat in url)
        csv_text, status_error = responses_by_satellite[satellite]
        response = MagicMock()
        response.text = csv_text
        if status_error:
            response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "erreur simulée", request=MagicMock(), response=MagicMock()
            )
        else:
            response.raise_for_status = MagicMock()
        return response

    mock_client.get = AsyncMock(side_effect=fake_get)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    mocker.patch("app.services.fire_data_source.httpx.AsyncClient", return_value=mock_client)
    return mock_client


@pytest.mark.asyncio
async def test_fetch_recent_queries_all_default_satellites(mocker):
    make_mock_client(mocker, {
        "VIIRS_SNPP_NRT": (VIIRS_CSV, False),
        "MODIS_NRT": (MODIS_CSV, False),
    })

    service = FirmsFetcherService(api_key="fake_key", bbox="46.5,-22.5,47.8,-20.5")
    results = await service.fetch_recent(day_range=1)

    assert len(results) == 2
    satellites_seen = {r.satellite for r in results}
    assert satellites_seen == {"VIIRS_SNPP_NRT", "MODIS_NRT"}


@pytest.mark.asyncio
async def test_fetch_recent_reads_brightness_from_correct_column_per_satellite(mocker):
    make_mock_client(mocker, {
        "VIIRS_SNPP_NRT": (VIIRS_CSV, False),
        "MODIS_NRT": (MODIS_CSV, False),
    })

    service = FirmsFetcherService(api_key="fake_key", bbox="46.5,-22.5,47.8,-20.5")
    results = await service.fetch_recent(day_range=1)

    viirs_result = next(r for r in results if r.satellite == "VIIRS_SNPP_NRT")
    modis_result = next(r for r in results if r.satellite == "MODIS_NRT")

    assert viirs_result.brightness == 310.5
    assert modis_result.brightness == 330.2


@pytest.mark.asyncio
async def test_fetch_recent_continues_when_one_satellite_fails(mocker):
    make_mock_client(mocker, {
        "VIIRS_SNPP_NRT": (VIIRS_CSV, False),
        "MODIS_NRT": ("", True),
    })

    service = FirmsFetcherService(api_key="fake_key", bbox="46.5,-22.5,47.8,-20.5")
    results = await service.fetch_recent(day_range=1)

    assert len(results) == 1
    assert results[0].satellite == "VIIRS_SNPP_NRT"


@pytest.mark.asyncio
async def test_fetch_recent_raises_when_all_satellites_fail(mocker):
    make_mock_client(mocker, {
        "VIIRS_SNPP_NRT": ("", True),
        "MODIS_NRT": ("", True),
    })

    service = FirmsFetcherService(api_key="fake_key", bbox="46.5,-22.5,47.8,-20.5")

    with pytest.raises(FireDataSourceError):
        await service.fetch_recent(day_range=1)


@pytest.mark.asyncio
async def test_fetch_recent_skips_malformed_rows(mocker):
    csv_with_bad_row = (
        "latitude,longitude,bright_ti4,confidence,acq_date,acq_time,frp\n"
        "-21.45,47.08,310.5,high,2026-08-01,1415,12.3\n"
        "PAS_UN_NOMBRE,47.09,300.0,low,2026-08-01,1420,8.1\n"
    )
    make_mock_client(mocker, {
        "VIIRS_SNPP_NRT": (csv_with_bad_row, False),
        "MODIS_NRT": ("latitude,longitude,acq_date,acq_time\n", False),
    })

    service = FirmsFetcherService(api_key="fake_key", bbox="46.5,-22.5,47.8,-20.5")
    results = await service.fetch_recent(day_range=1)

    assert len(results) == 1


@pytest.mark.asyncio
async def test_fetch_recent_raises_domain_error_when_api_key_missing(mocker):
    service = FirmsFetcherService(api_key="", bbox="46.5,-22.5,47.8,-20.5")
    with pytest.raises(FireDataSourceError):
        await service.fetch_recent(day_range=1)


@pytest.mark.asyncio
async def test_custom_satellites_list_overrides_default(mocker):
    make_mock_client(mocker, {"VIIRS_SNPP_NRT": (VIIRS_CSV, False)})

    service = FirmsFetcherService(
        api_key="fake_key", bbox="46.5,-22.5,47.8,-20.5", satellites=["VIIRS_SNPP_NRT"]
    )
    results = await service.fetch_recent(day_range=1)

    assert len(results) == 1
    assert results[0].satellite == "VIIRS_SNPP_NRT"
