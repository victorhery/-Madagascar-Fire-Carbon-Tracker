import datetime

from app.models import FireDetection


def test_recent_fires_empty_db_returns_empty_collection(client):
    """Base vide (job de polling pas encore lancé) -> collection vide, pas une erreur."""
    response = client.get("/api/v1/fires/recent")

    assert response.status_code == 200
    body = response.json()
    assert body["type"] == "FeatureCollection"
    assert body["features"] == []


def test_recent_fires_returns_geojson_from_db(client, db_session):
    db_session.add(FireDetection(
        latitude=-21.45, longitude=47.08, brightness=310.5, confidence="high",
        frp=12.3, acq_date=datetime.date.today(), acq_time="1415",
        satellite="VIIRS_SNPP_NRT",
    ))
    db_session.commit()

    response = client.get("/api/v1/fires/recent")

    assert response.status_code == 200
    body = response.json()
    assert len(body["features"]) == 1

    feature = body["features"][0]
    assert feature["type"] == "Feature"
    assert feature["geometry"]["coordinates"] == [47.08, -21.45]  # [lon, lat]
    assert feature["properties"]["brightness"] == 310.5
    assert feature["properties"]["confidence"] == "high"


def test_recent_fires_excludes_old_detections(client, db_session):
    old_date = datetime.date.today() - datetime.timedelta(days=10)
    db_session.add(FireDetection(
        latitude=-21.0, longitude=47.0, acq_date=old_date, acq_time="1000",
        satellite="VIIRS_SNPP_NRT",
    ))
    db_session.commit()

    response = client.get("/api/v1/fires/recent?day_range=1")

    assert response.status_code == 200
    assert response.json()["features"] == []
