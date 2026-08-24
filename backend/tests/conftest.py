import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import Base, get_db

# Force l'enregistrement des modèles sur Base.metadata avant tout
# create_all() dans les fixtures ci-dessous, quel que soit l'ordre
# d'import des fichiers de test.
from app.models import FireDetection, BurnedArea, Alert  # noqa: F401

# DB de test : SQLite en mémoire, recréée à chaque test pour l'isolation.
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture()
def db_session():
    # StaticPool = une seule connexion partagée, même depuis un autre thread.
    # Indispensable ici : FastAPI exécute les routes synchrones (def, pas
    # async def) dans un threadpool séparé. Sans StaticPool, ce thread
    # obtiendrait une base SQLite en mémoire DIFFÉRENTE (vide, sans tables)
    # à chaque connexion -> erreur "no such table" uniquement via TestClient.
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
