import datetime

import pytest
from sqlalchemy.exc import IntegrityError, StatementError

from app.models import Alert, AlertLevel, BurnedArea, FireDetection


def make_fire_detection(**overrides) -> FireDetection:
    defaults = dict(
        latitude=-21.45,
        longitude=47.08,
        brightness=310.5,
        confidence="high",
        frp=12.3,
        acq_date=datetime.date(2026, 8, 1),
        acq_time="1415",
        satellite="VIIRS_SNPP_NRT",
    )
    defaults.update(overrides)
    return FireDetection(**defaults)


def test_create_fire_detection(db_session):
    fire = make_fire_detection()
    db_session.add(fire)
    db_session.commit()

    saved = db_session.query(FireDetection).first()
    assert saved.id is not None
    assert saved.latitude == -21.45
    assert saved.longitude == 47.08
    assert saved.acq_date == datetime.date(2026, 8, 1)
    assert saved.created_at is not None


def test_duplicate_fire_detection_is_rejected(db_session):
    """
    Deux détections avec les mêmes (lat, lon, acq_date, acq_time, satellite)
    doivent être rejetées par la contrainte d'unicité -> essentiel pour que
    le job de polling FIRMS (Phase 4) ne crée pas de doublons.
    """
    db_session.add(make_fire_detection())
    db_session.commit()

    db_session.add(make_fire_detection())  # exact même clé de dédup
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_different_time_is_not_a_duplicate(db_session):
    """Une détection à un acq_time différent doit être acceptée normalement."""
    db_session.add(make_fire_detection(acq_time="1415"))
    db_session.commit()

    db_session.add(make_fire_detection(acq_time="1730"))
    db_session.commit()  # ne doit PAS lever d'erreur

    assert db_session.query(FireDetection).count() == 2


def test_create_burned_area_linked_to_fire_detection(db_session):
    fire = make_fire_detection()
    db_session.add(fire)
    db_session.commit()

    burned_area = BurnedArea(
        region="Haute Matsiatra",
        area_hectares=18.0,
        carbon_tons_estimate=145.0,
        period_start=datetime.date(2026, 7, 20),
        period_end=datetime.date(2026, 7, 27),
        fire_detection_id=fire.id,
    )
    db_session.add(burned_area)
    db_session.commit()

    saved = db_session.query(BurnedArea).first()
    assert saved.region == "Haute Matsiatra"
    assert saved.fire_detection.id == fire.id  # relation FK fonctionnelle


def test_create_alert_defaults(db_session):
    alert = Alert(
        region="Ihorombe",
        level=AlertLevel.HIGH,
        message="Forte densité de détections sur 24h",
    )
    db_session.add(alert)
    db_session.commit()

    saved = db_session.query(Alert).first()
    assert saved.level == AlertLevel.HIGH
    assert saved.resolved is False  # valeur par défaut
    assert saved.triggered_at is not None


def test_alert_level_rejects_invalid_value(db_session):
    """
    Une valeur de niveau hors de l'Enum doit être rejetée. Grâce à
    validate_strings=True, SQLAlchemy la détecte côté client, avant même
    d'envoyer la requête SQL (StatementError). La construction de l'objet
    Python, elle, ne lève rien : c'est le commit qui doit échouer.
    """
    alert = Alert(region="Vatovavy", level="extreme", message="Valeur invalide")
    db_session.add(alert)
    with pytest.raises(StatementError):
        db_session.commit()
    db_session.rollback()