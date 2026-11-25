import datetime

from app.models import BurnedArea
from app.repositories import SQLAlchemyBurnedAreaRepository


def test_latest_by_region_and_source_keeps_both_sources_separately(db_session):
    repo = SQLAlchemyBurnedAreaRepository(db_session)

    repo.create(BurnedArea(
        region="COFAV", area_hectares=5559.68, carbon_tons_estimate=833952.07,
        period_start=datetime.date(2026, 8, 30), period_end=datetime.date(2026, 9, 1),
        source="sentinel2",
    ))
    repo.create(BurnedArea(
        region="COFAV", area_hectares=2011.03, carbon_tons_estimate=301655.0,
        period_start=datetime.date(2026, 5, 25), period_end=datetime.date(2026, 9, 2),
        source="modis",
    ))

    rows = repo.latest_by_region_and_source()

    assert len(rows) == 2
    by_source = {r.source: r for r in rows}
    assert by_source["sentinel2"].area_hectares == 5559.68
    assert by_source["modis"].area_hectares == 2011.03


def test_latest_by_region_and_source_collapses_many_test_runs_to_one_per_source(db_session):
    """Reproduit le cas réel : 3 runs Sentinel-2 + 6 runs MODIS de test ->
    doit renvoyer seulement 2 lignes (1 par source), pas 9."""
    repo = SQLAlchemyBurnedAreaRepository(db_session)

    for area in (101826.71, 5559.68, 5559.68):
        repo.create(BurnedArea(
            region="COFAV", area_hectares=area, carbon_tons_estimate=area * 150,
            period_start=datetime.date(2026, 8, 1), period_end=datetime.date(2026, 9, 1),
            source="sentinel2",
        ))
    for area in (2011.03, 0.0, 2011.03, 0.0, 2011.03, 0.0):
        repo.create(BurnedArea(
            region="COFAV", area_hectares=area, carbon_tons_estimate=area * 150,
            period_start=datetime.date(2026, 5, 1), period_end=datetime.date(2026, 9, 2),
            source="modis",
        ))

    rows = repo.latest_by_region_and_source()

    assert len(rows) == 2  # pas 9
    by_source = {r.source: r for r in rows}
    assert by_source["sentinel2"].area_hectares == 5559.68  # dernier non-nul
    assert by_source["modis"].area_hectares == 2011.03       # dernier non-nul (le 0 final est ignoré)


def test_latest_by_region_and_source_sorts_sentinel2_before_modis(db_session):
    repo = SQLAlchemyBurnedAreaRepository(db_session)
    repo.create(BurnedArea(
        region="COFAV", area_hectares=100.0, carbon_tons_estimate=15000.0,
        period_start=datetime.date(2026, 8, 1), period_end=datetime.date(2026, 9, 1),
        source="modis",
    ))
    repo.create(BurnedArea(
        region="COFAV", area_hectares=50.0, carbon_tons_estimate=7500.0,
        period_start=datetime.date(2026, 8, 1), period_end=datetime.date(2026, 9, 1),
        source="sentinel2",
    ))

    rows = repo.latest_by_region_and_source()

    assert [r.source for r in rows] == ["sentinel2", "modis"]
