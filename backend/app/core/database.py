from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings

# Responsabilité unique : gérer la connexion et les sessions SQLAlchemy.
# Ce module ne connaît rien de FIRMS, GEE, ni des modèles métier.

# `connect_args`/`poolclass` avec check_same_thread=False et StaticPool ne
# sont nécessaires QUE pour SQLite (utilisé dans les tests). En Postgres,
# ces arguments sont ignorés si absents.
engine_kwargs = {}
if settings.DATABASE_URL.startswith("sqlite"):
    engine_kwargs = {
        "connect_args": {"check_same_thread": False},
        "poolclass": StaticPool,
    }

engine = create_engine(settings.DATABASE_URL, **engine_kwargs)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Toutes les futures classes de modèles (FireDetection, BurnedArea, Alert...)
# hériteront de cette Base (Phase 1).
Base = declarative_base()


def get_db() -> Generator:
    """
    Dépendance FastAPI (principe D de SOLID : les routes dépendent de cette
    abstraction, jamais directement de `engine` ou `SessionLocal`).
    Permet de remplacer facilement la DB réelle par une DB de test
    (voir tests/conftest.py -> app.dependency_overrides[get_db]).
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
