from app.models import Alert, AlertLevel


def test_active_alerts_empty_db_returns_empty_list(client):
    response = client.get("/api/v1/alerts/active")

    assert response.status_code == 200
    assert response.json() == []


def test_active_alerts_excludes_resolved(client, db_session):
    db_session.add(Alert(region="Ihorombe", level=AlertLevel.HIGH, message="Active"))
    db_session.add(Alert(region="Vatovavy", level=AlertLevel.LOW, message="Résolue", resolved=True))
    db_session.commit()

    response = client.get("/api/v1/alerts/active")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["region"] == "Ihorombe"
    assert body[0]["level"] == "high"
