import datetime

from app.models import BurnedArea


def test_carbon_history_empty_db_returns_empty_list(client):
    response = client.get("/api/v1/carbon/history")

    assert response.status_code == 200
    assert response.json() == []


def test_carbon_history_excludes_old_window_scans(client, db_session):
    today = datetime.date.today()

    db_session.add(BurnedArea(  # ancien scan "blob" (3 semaines) -> exclu
        region="COFAV", area_hectares=123072.8, carbon_tons_estimate=18460914.0,
        period_start=today - datetime.timedelta(days=21), period_end=today,
        source="sentinel2",
    ))
    db_session.add(BurnedArea(  # vraie ligne quotidienne -> incluse
        region="COFAV", area_hectares=10.0, carbon_tons_estimate=1500.0,
        period_start=today, period_end=today,
        source="sentinel2",
    ))
    db_session.commit()

    response = client.get("/api/v1/carbon/history")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["area_hectares"] == 10.0
