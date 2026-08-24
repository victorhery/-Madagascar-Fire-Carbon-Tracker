import datetime
from unittest.mock import MagicMock

from app.jobs.estimate_burned_area import run_estimate_burned_area
from app.models import BurnedArea
from app.repositories import SQLAlchemyBurnedAreaRepository
from app.services import RawBurnedAreaEstimate


def test_run_estimate_burned_area_persists_result(db_session):
    source = MagicMock()
    source.estimate_burned_area.return_value = RawBurnedAreaEstimate(
        region="Ihorombe",
        area_hectares=42.0,
        carbon_tons_estimate=6300.0,
        period_start=datetime.date(2026, 7, 20),
        period_end=datetime.date(2026, 7, 27),
    )
    repo = SQLAlchemyBurnedAreaRepository(db_session)

    result = run_estimate_burned_area(
        source, repo,
        region="Ihorombe", bbox=(46.5, -22.5, 47.8, -20.5),
        period_start=datetime.date(2026, 7, 20), period_end=datetime.date(2026, 7, 27),
    )

    assert result.id is not None
    assert db_session.query(BurnedArea).count() == 1
    saved = db_session.query(BurnedArea).first()
    assert saved.region == "Ihorombe"
    assert saved.area_hectares == 42.0
    assert saved.carbon_tons_estimate == 6300.0


def test_run_estimate_burned_area_passes_correct_arguments_to_source(db_session):
    source = MagicMock()
    source.estimate_burned_area.return_value = RawBurnedAreaEstimate(
        region="Vatovavy", area_hectares=0.0, carbon_tons_estimate=0.0,
        period_start=datetime.date(2026, 8, 1), period_end=datetime.date(2026, 8, 8),
    )
    repo = SQLAlchemyBurnedAreaRepository(db_session)

    run_estimate_burned_area(
        source, repo,
        region="Vatovavy", bbox=(46.0, -23.0, 48.0, -20.0),
        period_start=datetime.date(2026, 8, 1), period_end=datetime.date(2026, 8, 8),
    )

    source.estimate_burned_area.assert_called_once_with(
        region="Vatovavy", bbox=(46.0, -23.0, 48.0, -20.0),
        period_start=datetime.date(2026, 8, 1), period_end=datetime.date(2026, 8, 8),
    )
