import datetime

from app.jobs.generate_alerts import determine_alert_level, run_generate_alerts
from app.models import Alert, AlertLevel, FireDetection
from app.repositories import SQLAlchemyAlertRepository, SQLAlchemyFireRepository


def test_determine_alert_level_thresholds():
    assert determine_alert_level(0) is None
    assert determine_alert_level(4) is None
    assert determine_alert_level(5) == AlertLevel.LOW
    assert determine_alert_level(14) == AlertLevel.LOW
    assert determine_alert_level(15) == AlertLevel.MEDIUM
    assert determine_alert_level(29) == AlertLevel.MEDIUM
    assert determine_alert_level(30) == AlertLevel.HIGH
    assert determine_alert_level(100) == AlertLevel.HIGH


def _add_detections(db_session, count: int) -> None:
    for i in range(count):
        db_session.add(FireDetection(
            latitude=-21.0 + i * 0.001, longitude=47.0, acq_date=datetime.date.today(),
            acq_time=f"{1000 + i}", satellite="VIIRS_SNPP_NRT",
        ))
    db_session.commit()


def test_run_generate_alerts_creates_alert_when_threshold_exceeded(db_session):
    _add_detections(db_session, count=20)  # -> MEDIUM (>= 15)

    fire_repo = SQLAlchemyFireRepository(db_session)
    alert_repo = SQLAlchemyAlertRepository(db_session)

    alert = run_generate_alerts(fire_repo, alert_repo)

    assert alert is not None
    assert alert.level == AlertLevel.MEDIUM
    assert alert.region == "COFAV"
    assert db_session.query(Alert).count() == 1


def test_run_generate_alerts_returns_none_below_threshold(db_session):
    _add_detections(db_session, count=2)  # sous le seuil LOW (5)

    fire_repo = SQLAlchemyFireRepository(db_session)
    alert_repo = SQLAlchemyAlertRepository(db_session)

    alert = run_generate_alerts(fire_repo, alert_repo)

    assert alert is None
    assert db_session.query(Alert).count() == 0
