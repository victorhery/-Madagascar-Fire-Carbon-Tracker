import datetime

from app.models import BurnedArea
from app.repositories import SQLAlchemyBurnedAreaRepository


def test_latest_by_region_prefers_sentinel2_over_more_recent_modis(db_session):
    repo = SQLAlchemyBurnedAreaRepository(db_session)

    older_sentinel2 = repo.create(BurnedArea(
        region="COFAV", area_hectares=21.0, carbon_tons_estimate=3150.0,
        period_start=datetime.date(2026, 8, 1), period_end=datetime.date(2026, 8, 15),
        source="sentinel2",
    ))
    repo.create(BurnedArea(
        region="COFAV", area_hectares=999.0, carbon_tons_estimate=149850.0,
        period_start=datetime.date(2026, 4, 1), period_end=datetime.date(2026, 6, 1),
        source="modis",
    ))

    latest = repo.latest_by_region()

    assert len(latest) == 1
    assert latest[0].id == older_sentinel2.id
    assert latest[0].source == "sentinel2"


def test_latest_by_region_falls_back_to_modis_when_no_sentinel2(db_session):
    repo = SQLAlchemyBurnedAreaRepository(db_session)
    repo.create(BurnedArea(
        region="Ihorombe", area_hectares=42.0, carbon_tons_estimate=6300.0,
        period_start=datetime.date(2025, 8, 1), period_end=datetime.date(2025, 12, 1),
        source="modis",
    ))

    latest = repo.latest_by_region()

    assert len(latest) == 1
    assert latest[0].source == "modis"
    assert latest[0].area_hectares == 42.0


def test_latest_by_region_handles_multiple_regions_independently(db_session):
    repo = SQLAlchemyBurnedAreaRepository(db_session)
    repo.create(BurnedArea(
        region="Ihorombe", area_hectares=42.0, carbon_tons_estimate=6300.0,
        period_start=datetime.date(2025, 8, 1), period_end=datetime.date(2025, 12, 1),
        source="modis",
    ))
    repo.create(BurnedArea(
        region="Vatovavy", area_hectares=12.0, carbon_tons_estimate=1800.0,
        period_start=datetime.date(2026, 8, 1), period_end=datetime.date(2026, 8, 15),
        source="sentinel2",
    ))

    latest = repo.latest_by_region()
    by_region = {row.region: row for row in latest}

    assert len(latest) == 2
    assert by_region["Ihorombe"].source == "modis"
    assert by_region["Vatovavy"].source == "sentinel2"


def test_totals_latest_per_region_sums_the_selected_rows(db_session):
    repo = SQLAlchemyBurnedAreaRepository(db_session)
    repo.create(BurnedArea(
        region="Ihorombe", area_hectares=42.0, carbon_tons_estimate=6300.0,
        period_start=datetime.date(2025, 8, 1), period_end=datetime.date(2025, 12, 1),
        source="modis",
    ))
    repo.create(BurnedArea(
        region="Vatovavy", area_hectares=12.0, carbon_tons_estimate=1800.0,
        period_start=datetime.date(2026, 8, 1), period_end=datetime.date(2026, 8, 15),
        source="sentinel2",
    ))
    repo.create(BurnedArea(
        region="Vatovavy", area_hectares=500.0, carbon_tons_estimate=75000.0,
        period_start=datetime.date(2025, 8, 1), period_end=datetime.date(2025, 12, 1),
        source="modis",
    ))

    area_total, carbon_total = repo.totals_latest_per_region()

    assert area_total == 54.0
    assert carbon_total == 8100.0


def test_latest_by_region_does_not_let_a_later_zero_result_overwrite_a_real_one(db_session):
    repo = SQLAlchemyBurnedAreaRepository(db_session)

    repo.create(BurnedArea(
        region="COFAV", area_hectares=101826.71, carbon_tons_estimate=15274006.88,
        period_start=datetime.date(2026, 8, 11), period_end=datetime.date(2026, 9, 1),
        source="sentinel2",
    ))
    repo.create(BurnedArea(
        region="COFAV", area_hectares=5559.68, carbon_tons_estimate=833952.07,
        period_start=datetime.date(2026, 8, 28), period_end=datetime.date(2026, 9, 1),
        source="sentinel2",
    ))
    repo.create(BurnedArea(
        region="COFAV", area_hectares=5559.68, carbon_tons_estimate=833952.07,
        period_start=datetime.date(2026, 8, 30), period_end=datetime.date(2026, 9, 1),
        source="sentinel2",
    ))
    last_zero_run = repo.create(BurnedArea(
        region="COFAV", area_hectares=0.0, carbon_tons_estimate=0.0,
        period_start=datetime.date(2026, 8, 31), period_end=datetime.date(2026, 9, 1),
        source="sentinel2",
    ))

    latest = repo.latest_by_region()

    assert len(latest) == 1
    assert latest[0].id != last_zero_run.id
    assert latest[0].area_hectares == 5559.68


def test_latest_by_region_returns_zero_result_only_when_it_is_the_only_one(db_session):
    repo = SQLAlchemyBurnedAreaRepository(db_session)
    only_run = repo.create(BurnedArea(
        region="COFAV", area_hectares=0.0, carbon_tons_estimate=0.0,
        period_start=datetime.date(2026, 8, 31), period_end=datetime.date(2026, 9, 1),
        source="sentinel2",
    ))

    latest = repo.latest_by_region()

    assert len(latest) == 1
    assert latest[0].id == only_run.id
    assert latest[0].area_hectares == 0.0
