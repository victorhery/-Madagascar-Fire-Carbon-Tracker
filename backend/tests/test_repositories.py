import datetime

from app.models import Alert, AlertLevel, BurnedArea, FireDetection
from app.repositories import (
    SQLAlchemyAlertRepository,
    SQLAlchemyBurnedAreaRepository,
    SQLAlchemyFireRepository,
)


# ---------- FireRepository ----------

def test_fire_repository_create_and_get_by_id(db_session):
    repo = SQLAlchemyFireRepository(db_session)
    fire = FireDetection(
        latitude=-21.45, longitude=47.08, acq_date=datetime.date(2026, 8, 1),
        acq_time="1415", satellite="VIIRS_SNPP_NRT",
    )

    created = repo.create(fire)
    assert created.id is not None

    fetched = repo.get_by_id(created.id)
    assert fetched is not None
    assert fetched.latitude == -21.45


def test_fire_repository_get_by_id_missing_returns_none(db_session):
    repo = SQLAlchemyFireRepository(db_session)
    assert repo.get_by_id(9999) is None


def test_fire_repository_get_by_natural_key(db_session):
    repo = SQLAlchemyFireRepository(db_session)
    fire = FireDetection(
        latitude=-21.45, longitude=47.08, acq_date=datetime.date(2026, 8, 1),
        acq_time="1415", satellite="VIIRS_SNPP_NRT",
    )
    repo.create(fire)

    found = repo.get_by_natural_key(
        latitude=-21.45, longitude=47.08, acq_date=datetime.date(2026, 8, 1),
        acq_time="1415", satellite="VIIRS_SNPP_NRT",
    )
    assert found is not None

    not_found = repo.get_by_natural_key(
        latitude=-21.45, longitude=47.08, acq_date=datetime.date(2026, 8, 1),
        acq_time="1999", satellite="VIIRS_SNPP_NRT",  # heure différente
    )
    assert not_found is None


def test_fire_repository_list_recent_filters_by_date(db_session):
    repo = SQLAlchemyFireRepository(db_session)
    repo.create(FireDetection(
        latitude=-21.0, longitude=47.0, acq_date=datetime.date(2026, 7, 1),
        acq_time="1000", satellite="VIIRS_SNPP_NRT",
    ))
    repo.create(FireDetection(
        latitude=-21.1, longitude=47.1, acq_date=datetime.date(2026, 8, 10),
        acq_time="1000", satellite="VIIRS_SNPP_NRT",
    ))

    recent = repo.list_recent(since=datetime.date(2026, 8, 1))
    assert len(recent) == 1
    assert recent[0].acq_date == datetime.date(2026, 8, 10)


# ---------- BurnedAreaRepository ----------

def test_burned_area_repository_create_and_list_by_region(db_session):
    repo = SQLAlchemyBurnedAreaRepository(db_session)
    repo.create(BurnedArea(
        region="Ihorombe", area_hectares=42.0, carbon_tons_estimate=180.0,
        period_start=datetime.date(2026, 7, 20), period_end=datetime.date(2026, 7, 27),
    ))
    repo.create(BurnedArea(
        region="Vatovavy", area_hectares=12.0, carbon_tons_estimate=95.0,
        period_start=datetime.date(2026, 7, 20), period_end=datetime.date(2026, 7, 27),
    ))

    ihorombe_only = repo.list_by_region("Ihorombe")
    assert len(ihorombe_only) == 1
    assert ihorombe_only[0].area_hectares == 42.0


def test_burned_area_repository_list_recent(db_session):
    repo = SQLAlchemyBurnedAreaRepository(db_session)
    repo.create(BurnedArea(
        region="Ihorombe", area_hectares=42.0, carbon_tons_estimate=180.0,
        period_start=datetime.date(2026, 6, 1), period_end=datetime.date(2026, 6, 10),
    ))
    repo.create(BurnedArea(
        region="Ihorombe", area_hectares=10.0, carbon_tons_estimate=50.0,
        period_start=datetime.date(2026, 8, 5), period_end=datetime.date(2026, 8, 12),
    ))

    recent = repo.list_recent(since=datetime.date(2026, 8, 1))
    assert len(recent) == 1
    assert recent[0].area_hectares == 10.0


# ---------- AlertRepository ----------

def test_alert_repository_create_and_list_active(db_session):
    repo = SQLAlchemyAlertRepository(db_session)
    active = Alert(region="Ihorombe", level=AlertLevel.HIGH, message="Zone critique")
    resolved = Alert(
        region="Vatovavy", level=AlertLevel.LOW, message="Résolue", resolved=True
    )
    repo.create(active)
    repo.create(resolved)

    active_alerts = repo.list_active()
    assert len(active_alerts) == 1
    assert active_alerts[0].region == "Ihorombe"


def test_alert_repository_list_by_region(db_session):
    repo = SQLAlchemyAlertRepository(db_session)
    repo.create(Alert(region="Ihorombe", level=AlertLevel.MEDIUM, message="A"))
    repo.create(Alert(region="Ihorombe", level=AlertLevel.HIGH, message="B"))
    repo.create(Alert(region="Vatovavy", level=AlertLevel.LOW, message="C"))

    ihorombe_alerts = repo.list_by_region("Ihorombe")
    assert len(ihorombe_alerts) == 2


# ---------- Méthodes d'agrégation (Phase 5) ----------

def test_fire_repository_count_since(db_session):
    repo = SQLAlchemyFireRepository(db_session)
    repo.create(FireDetection(
        latitude=-21.0, longitude=47.0, acq_date=datetime.date(2026, 8, 13),
        acq_time="1000", satellite="VIIRS_SNPP_NRT",
    ))
    repo.create(FireDetection(
        latitude=-21.1, longitude=47.1, acq_date=datetime.date(2026, 8, 1),
        acq_time="1000", satellite="VIIRS_SNPP_NRT",
    ))

    assert repo.count_since(since=datetime.date(2026, 8, 13)) == 1
    assert repo.count_since(since=datetime.date(2026, 8, 1)) == 2


def test_fire_repository_count_grouped_by_day(db_session):
    repo = SQLAlchemyFireRepository(db_session)
    repo.create(FireDetection(
        latitude=-21.0, longitude=47.0, acq_date=datetime.date(2026, 8, 13),
        acq_time="1000", satellite="VIIRS_SNPP_NRT",
    ))
    repo.create(FireDetection(
        latitude=-21.1, longitude=47.1, acq_date=datetime.date(2026, 8, 13),
        acq_time="1200", satellite="VIIRS_SNPP_NRT",
    ))
    repo.create(FireDetection(
        latitude=-21.2, longitude=47.2, acq_date=datetime.date(2026, 8, 12),
        acq_time="1000", satellite="VIIRS_SNPP_NRT",
    ))

    counts = repo.count_grouped_by_day(since=datetime.date(2026, 8, 1))
    assert counts[datetime.date(2026, 8, 13)] == 2
    assert counts[datetime.date(2026, 8, 12)] == 1


def test_burned_area_repository_totals(db_session):
    repo = SQLAlchemyBurnedAreaRepository(db_session)
    repo.create(BurnedArea(
        region="Ihorombe", area_hectares=42.0, carbon_tons_estimate=180.0,
        period_start=datetime.date(2026, 7, 20), period_end=datetime.date(2026, 7, 27),
    ))
    repo.create(BurnedArea(
        region="Vatovavy", area_hectares=12.0, carbon_tons_estimate=95.0,
        period_start=datetime.date(2026, 7, 20), period_end=datetime.date(2026, 7, 27),
    ))

    area_total, carbon_total = repo.totals()
    assert area_total == 54.0
    assert carbon_total == 275.0


def test_burned_area_repository_totals_empty_db_returns_zero(db_session):
    repo = SQLAlchemyBurnedAreaRepository(db_session)
    area_total, carbon_total = repo.totals()
    assert area_total == 0.0
    assert carbon_total == 0.0


def test_alert_repository_count_active(db_session):
    repo = SQLAlchemyAlertRepository(db_session)
    repo.create(Alert(region="Ihorombe", level=AlertLevel.HIGH, message="A"))
    repo.create(Alert(region="Vatovavy", level=AlertLevel.LOW, message="B", resolved=True))

    assert repo.count_active() == 1
