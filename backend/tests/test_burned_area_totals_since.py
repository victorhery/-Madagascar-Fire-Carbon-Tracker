import datetime

from app.models import BurnedArea
from app.repositories import SQLAlchemyBurnedAreaRepository


def test_totals_without_since_sums_everything(db_session):
    repo = SQLAlchemyBurnedAreaRepository(db_session)
    repo.create(BurnedArea(
        region="COFAV", area_hectares=100.0, carbon_tons_estimate=15000.0,
        period_start=datetime.date(2025, 8, 1), period_end=datetime.date(2025, 12, 1),
    ))
    repo.create(BurnedArea(
        region="COFAV", area_hectares=50.0, carbon_tons_estimate=7500.0,
        period_start=datetime.date(2026, 8, 1), period_end=datetime.date(2026, 8, 15),
    ))

    area_total, carbon_total = repo.totals()

    assert area_total == 150.0
    assert carbon_total == 22500.0


def test_totals_with_since_excludes_old_test_runs(db_session):
    """Reproduit le cas réel : un run de vérification Phase 6 (période
    ancienne) ne doit plus polluer le total affiché au dashboard."""
    repo = SQLAlchemyBurnedAreaRepository(db_session)
    repo.create(BurnedArea(  # ancien run de test, hors fenêtre
        region="COFAV", area_hectares=128985.0, carbon_tons_estimate=128985.0 * 150,
        period_start=datetime.date(2025, 8, 1), period_end=datetime.date(2025, 12, 1),
    ))
    repo.create(BurnedArea(  # run récent, dans la fenêtre
        region="COFAV", area_hectares=21.0, carbon_tons_estimate=21.0 * 150,
        period_start=datetime.date(2026, 8, 10), period_end=datetime.date(2026, 8, 24),
    ))

    since = datetime.date(2026, 8, 1)
    area_total, carbon_total = repo.totals(since=since)

    assert area_total == 21.0
    assert carbon_total == 21.0 * 150
