import datetime
from unittest.mock import MagicMock

from app.jobs.estimate_burned_area import run_estimate_burned_area
from app.repositories import SQLAlchemyBurnedAreaRepository
from app.services import RawBurnedAreaEstimate


def test_run_estimate_burned_area_stores_given_source_name(db_session):
    source = MagicMock()
    source.estimate_burned_area.return_value = RawBurnedAreaEstimate(
        region="COFAV", area_hectares=21.0, carbon_tons_estimate=3150.0,
        period_start=datetime.date(2026, 8, 1), period_end=datetime.date(2026, 8, 15),
    )
    repo = SQLAlchemyBurnedAreaRepository(db_session)

    result = run_estimate_burned_area(
        source, repo,
        region="COFAV", bbox=(46.5, -22.5, 47.8, -20.5),
        period_start=datetime.date(2026, 8, 1), period_end=datetime.date(2026, 8, 15),
        source_name="sentinel2",
    )

    assert result.source == "sentinel2"


def test_run_estimate_burned_area_defaults_to_modis_when_source_name_omitted(db_session):
    source = MagicMock()
    source.estimate_burned_area.return_value = RawBurnedAreaEstimate(
        region="COFAV", area_hectares=10.0, carbon_tons_estimate=1500.0,
        period_start=datetime.date(2026, 8, 1), period_end=datetime.date(2026, 8, 15),
    )
    repo = SQLAlchemyBurnedAreaRepository(db_session)

    result = run_estimate_burned_area(
        source, repo,
        region="COFAV", bbox=(46.5, -22.5, 47.8, -20.5),
        period_start=datetime.date(2026, 8, 1), period_end=datetime.date(2026, 8, 15),
    )

    assert result.source == "modis"
