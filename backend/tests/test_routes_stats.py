import datetime

from app.models import Alert, AlertLevel, BurnedArea, FireDetection


def test_stats_empty_db_returns_zeros(client):
    response = client.get("/api/v1/stats")

    assert response.status_code == 200
    body = response.json()
    assert body["active_fires_24h"] == 0
    assert body["active_fires_trend_7d"] == [0] * 7
    assert body["burned_area_hectares_total"] == 0.0
    assert body["co2_estimate_tons_total"] == 0.0
    assert body["active_alerts"] == 0


def test_stats_aggregates_all_three_repositories(client, db_session):
    today = datetime.date.today()

    db_session.add(FireDetection(
        latitude=-21.0, longitude=47.0, acq_date=today, acq_time="1000",
        satellite="VIIRS_SNPP_NRT",
    ))
    db_session.add(BurnedArea(
        region="Ihorombe", area_hectares=42.0, carbon_tons_estimate=180.0,
        period_start=today, period_end=today,
    ))
    db_session.add(Alert(region="Ihorombe", level=AlertLevel.HIGH, message="Zone critique"))
    db_session.commit()

    response = client.get("/api/v1/stats")

    assert response.status_code == 200
    body = response.json()
    assert body["active_fires_24h"] == 1
    assert body["active_fires_trend_7d"][-1] == 1  # dernier jour = aujourd'hui
    assert body["burned_area_hectares_total"] == 42.0
    assert body["co2_estimate_tons_total"] == 180.0
    assert body["active_alerts"] == 1
