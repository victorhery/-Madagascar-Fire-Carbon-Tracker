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


def _add_detections(db_session, count: int, start_index: int = 0) -> None:
    """
    Crée `count` détections toutes différentes.

    start_index évite les doublons lors d'un deuxième appel :
    - premier lot : index 0 à 19
    - second lot : index 20 à 34
    """
    for i in range(start_index, start_index + count):
        db_session.add(
            FireDetection(
                latitude=-21.0 + i * 0.001,
                longitude=47.0 + i * 0.001,
                acq_date=datetime.date.today(),
                acq_time=f"{1000 + i}",
                satellite="VIIRS_SNPP_NRT",
            )
        )
    db_session.commit()


def test_run_generate_alerts_creates_alert_when_threshold_exceeded(db_session):
    _add_detections(db_session, count=20)

    fire_repo = SQLAlchemyFireRepository(db_session)
    alert_repo = SQLAlchemyAlertRepository(db_session)

    alert = run_generate_alerts(fire_repo, alert_repo)

    assert alert is not None
    assert alert.level == AlertLevel.MEDIUM
    assert alert.region == "COFAV"
    assert db_session.query(Alert).count() == 1


def test_run_generate_alerts_updates_existing_active_alert_instead_of_creating_duplicate(
    db_session,
):
    _add_detections(db_session, count=20)

    fire_repo = SQLAlchemyFireRepository(db_session)
    alert_repo = SQLAlchemyAlertRepository(db_session)

    first_alert = run_generate_alerts(fire_repo, alert_repo)
    second_alert = run_generate_alerts(fire_repo, alert_repo)

    assert first_alert is not None
    assert second_alert is not None
    assert first_alert.id == second_alert.id
    assert db_session.query(Alert).count() == 1


def test_run_generate_alerts_updates_level_when_fire_count_increases(db_session):
    _add_detections(db_session, count=20)

    fire_repo = SQLAlchemyFireRepository(db_session)
    alert_repo = SQLAlchemyAlertRepository(db_session)

    first_alert = run_generate_alerts(fire_repo, alert_repo)

    assert first_alert is not None
    assert first_alert.level == AlertLevel.MEDIUM

    _add_detections(db_session, count=15, start_index=20)

    updated_alert = run_generate_alerts(fire_repo, alert_repo)

    assert updated_alert is not None
    assert updated_alert.id == first_alert.id
    assert updated_alert.level == AlertLevel.HIGH
    assert db_session.query(Alert).count() == 1


def test_run_generate_alerts_returns_none_below_threshold(db_session):
    _add_detections(db_session, count=2)

    fire_repo = SQLAlchemyFireRepository(db_session)
    alert_repo = SQLAlchemyAlertRepository(db_session)

    alert = run_generate_alerts(fire_repo, alert_repo)

    assert alert is None
    assert db_session.query(Alert).count() == 0