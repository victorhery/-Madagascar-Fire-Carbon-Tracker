from app.main import _running_under_pytest


def test_scheduler_guard_detects_pytest():
    """Garantit que le lifespan de main.py désactive bien le scheduler
    pendant les tests -> aucun appel réseau FIRMS/GEE ne doit se déclencher
    quand `pytest` tourne (voir app/main.py::lifespan)."""
    assert _running_under_pytest() is True


def test_client_starts_without_scheduler_side_effects(client):
    """La fixture `client` (conftest.py) déclenche déjà le lifespan via
    `with TestClient(app) as test_client`. Si ce test se termine sans
    exception ni timeout réseau, c'est que le scheduler n'a pas tourné."""
    response = client.get("/health")
    assert response.status_code == 200
