import datetime

from app.models import BurnedArea


def test_carbon_estimates_empty_db_returns_empty_list(client):
    response = client.get("/api/v1/carbon/estimates")

    assert response.status_code == 200
    assert response.json() == []


def test_carbon_estimates_returns_data_from_db(client, db_session):
    today = datetime.date.today()
    db_session.add(BurnedArea(
        region="Ihorombe", area_hectares=42.0, carbon_tons_estimate=6300.0,
        period_start=today - datetime.timedelta(days=7), period_end=today,
    ))
    db_session.commit()

    response = client.get("/api/v1/carbon/estimates")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["region"] == "Ihorombe"
    assert body[0]["area_hectares"] == 42.0
    assert body[0]["carbon_tons_estimate"] == 6300.0
