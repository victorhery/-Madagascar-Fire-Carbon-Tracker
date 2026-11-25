import datetime

from app.models import BurnedArea
from app.repositories import SQLAlchemyBurnedAreaRepository


def test_shows_todays_fire_when_detected_today(db_session):
    """S'il y a un feu aujourd'hui -> c'est CELUI-LÀ qui s'affiche."""
    repo = SQLAlchemyBurnedAreaRepository(db_session)
    today = datetime.date(2026, 9, 16)

    repo.create(BurnedArea(
        region="COFAV", area_hectares=50.0, carbon_tons_estimate=7500.0,
        period_start=today - datetime.timedelta(days=3), period_end=today - datetime.timedelta(days=3),
        source="sentinel2",
    ))
    repo.create(BurnedArea(
        region="COFAV", area_hectares=12.5, carbon_tons_estimate=1875.0,
        period_start=today, period_end=today,
        source="sentinel2",
    ))

    latest = repo.latest_daily_by_region()

    assert len(latest) == 1
    assert latest[0].period_start == today
    assert latest[0].area_hectares == 12.5


def test_shows_last_known_fire_when_nothing_new_today(db_session):
    """S'il n'y a rien de nouveau aujourd'hui -> le dernier feu connu
    (hier, avant-hier...) reste affiché, pas de trou/zéro artificiel."""
    repo = SQLAlchemyBurnedAreaRepository(db_session)
    three_days_ago = datetime.date(2026, 9, 13)

    only_known_fire = repo.create(BurnedArea(
        region="COFAV", area_hectares=5.6, carbon_tons_estimate=840.0,
        period_start=three_days_ago, period_end=three_days_ago,
        source="sentinel2",
    ))

    latest = repo.latest_daily_by_region()

    assert len(latest) == 1
    assert latest[0].id == only_known_fire.id
    assert latest[0].period_start == three_days_ago


def test_prefers_sentinel2_even_if_modis_day_is_more_recent(db_session):
    """Décision produit déjà validée : Sentinel-2 reste prioritaire même
    si un jour MODIS plus récent existe -> confirmé encore valable ici."""
    repo = SQLAlchemyBurnedAreaRepository(db_session)

    repo.create(BurnedArea(
        region="COFAV", area_hectares=100.0, carbon_tons_estimate=15000.0,
        period_start=datetime.date(2026, 9, 15), period_end=datetime.date(2026, 9, 15),
        source="modis",  # plus récent en date, mais pas la source préférée
    ))
    sentinel_row = repo.create(BurnedArea(
        region="COFAV", area_hectares=12.5, carbon_tons_estimate=1875.0,
        period_start=datetime.date(2026, 9, 10), period_end=datetime.date(2026, 9, 10),
        source="sentinel2",
    ))

    latest = repo.latest_daily_by_region()

    assert len(latest) == 1
    assert latest[0].id == sentinel_row.id


def test_ignores_old_window_scan_rows(db_session):
    """Un ancien scan 'blob' (period_start != period_end) ne doit jamais
    être choisi comme 'dernier feu' -> seules les vraies lignes
    quotidiennes comptent."""
    repo = SQLAlchemyBurnedAreaRepository(db_session)
    repo.create(BurnedArea(
        region="COFAV", area_hectares=101826.71, carbon_tons_estimate=15274006.88,
        period_start=datetime.date(2026, 8, 25), period_end=datetime.date(2026, 9, 15),
        source="sentinel2",
    ))
    real_daily_row = repo.create(BurnedArea(
        region="COFAV", area_hectares=5.6, carbon_tons_estimate=840.0,
        period_start=datetime.date(2026, 9, 9), period_end=datetime.date(2026, 9, 9),
        source="sentinel2",
    ))

    latest = repo.latest_daily_by_region()

    assert len(latest) == 1
    assert latest[0].id == real_daily_row.id
