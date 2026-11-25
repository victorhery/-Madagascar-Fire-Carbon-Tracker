import datetime
from unittest.mock import MagicMock

from app.jobs.estimate_burned_area import run_estimate_burned_area_daily
from app.services import RawBurnedAreaEstimate
from app.models import BurnedArea
from app.repositories import SQLAlchemyBurnedAreaRepository


def test_run_daily_creates_one_row_per_day(db_session):
    source = MagicMock()
    source.estimate_burned_area_daily.return_value = [
        RawBurnedAreaEstimate(
            region="COFAV", area_hectares=10.0, carbon_tons_estimate=1500.0,
            period_start=datetime.date(2026, 9, 12), period_end=datetime.date(2026, 9, 12),
        ),
        RawBurnedAreaEstimate(
            region="COFAV", area_hectares=25.0, carbon_tons_estimate=3750.0,
            period_start=datetime.date(2026, 9, 13), period_end=datetime.date(2026, 9, 13),
        ),
    ]
    repo = SQLAlchemyBurnedAreaRepository(db_session)

    created = run_estimate_burned_area_daily(
        source, repo, region="COFAV", bbox=(46.5, -22.5, 47.8, -20.5),
        period_start=datetime.date(2026, 9, 12), period_end=datetime.date(2026, 9, 15),
        source_name="sentinel2",
    )

    assert len(created) == 2
    assert db_session.query(BurnedArea).count() == 2


def test_run_daily_skips_days_already_in_base(db_session):
    """Rejoue la même fenêtre (chevauchement, comme le fait le scheduler
    tous les jours) -> aucun doublon créé pour un jour déjà connu."""
    source = MagicMock()
    source.estimate_burned_area_daily.return_value = [
        RawBurnedAreaEstimate(
            region="COFAV", area_hectares=10.0, carbon_tons_estimate=1500.0,
            period_start=datetime.date(2026, 9, 12), period_end=datetime.date(2026, 9, 12),
        ),
    ]
    repo = SQLAlchemyBurnedAreaRepository(db_session)

    first_run = run_estimate_burned_area_daily(
        source, repo, region="COFAV", bbox=(46.5, -22.5, 47.8, -20.5),
        period_start=datetime.date(2026, 9, 1), period_end=datetime.date(2026, 9, 15),
        source_name="sentinel2",
    )
    second_run = run_estimate_burned_area_daily(  # même jour redétecté par une fenêtre glissante
        source, repo, region="COFAV", bbox=(46.5, -22.5, 47.8, -20.5),
        period_start=datetime.date(2026, 9, 5), period_end=datetime.date(2026, 9, 16),
        source_name="sentinel2",
    )

    assert len(first_run) == 1
    assert len(second_run) == 0  # rien de nouveau, déjà en base
    assert db_session.query(BurnedArea).count() == 1


def test_total_by_day_preferred_avoids_double_counting_same_day_both_sources(db_session):
    repo = SQLAlchemyBurnedAreaRepository(db_session)
    repo.create(BurnedArea(
        region="COFAV", area_hectares=100.0, carbon_tons_estimate=15000.0,
        period_start=datetime.date(2026, 9, 12), period_end=datetime.date(2026, 9, 12),
        source="modis",
    ))
    repo.create(BurnedArea(
        region="COFAV", area_hectares=120.0, carbon_tons_estimate=18000.0,
        period_start=datetime.date(2026, 9, 12), period_end=datetime.date(2026, 9, 12),
        source="sentinel2",
    ))
    repo.create(BurnedArea(
        region="COFAV", area_hectares=50.0, carbon_tons_estimate=7500.0,
        period_start=datetime.date(2026, 9, 13), period_end=datetime.date(2026, 9, 13),
        source="modis",
    ))

    area_total, carbon_total = repo.total_by_day_preferred(since=datetime.date(2026, 9, 1))

    # 12/09 : sentinel2 préféré (120) au lieu de modis (100) -> pas les deux additionnés
    # 13/09 : seul modis dispo (50)
    assert area_total == 170.0
    assert carbon_total == 25500.0


def test_list_daily_history_excludes_old_window_scans(db_session):
    """Les anciens runs 'blob' (period_start != period_end, faits à la
    main avant ce changement) ne doivent JAMAIS apparaître dans l'historique
    quotidien -> seules les vraies lignes jour-par-jour comptent."""
    repo = SQLAlchemyBurnedAreaRepository(db_session)
    repo.create(BurnedArea(  # ancien run "blob" (3 semaines)
        region="COFAV", area_hectares=123072.8, carbon_tons_estimate=18460914.0,
        period_start=datetime.date(2026, 8, 25), period_end=datetime.date(2026, 9, 15),
        source="sentinel2",
    ))
    repo.create(BurnedArea(  # vraie ligne quotidienne
        region="COFAV", area_hectares=10.0, carbon_tons_estimate=1500.0,
        period_start=datetime.date(2026, 9, 12), period_end=datetime.date(2026, 9, 12),
        source="sentinel2",
    ))

    history = repo.list_daily_history(since=datetime.date(2026, 8, 1))

    assert len(history) == 1
    assert history[0].area_hectares == 10.0
