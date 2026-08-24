def test_health_returns_ok_when_db_reachable(client):
    """
    La DB de test (SQLite en mémoire, voir conftest.py) est toujours
    joignable dans ce test -> on attend un statut "ok".
    """
    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["database"] == "connected"


def test_health_response_shape(client):
    """Vérifie que le contrat de réponse ne change pas par accident."""
    response = client.get("/health")
    body = response.json()

    assert set(body.keys()) == {"status", "database"}
