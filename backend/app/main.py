from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.routes import alerts, carbon, fires, stats

app = FastAPI(title="Madagascar FireCarbon Tracker API")

# Configuration CORS pour autoriser le frontend Vue.js
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En dev, autorise toutes les origines
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(fires.router)
app.include_router(stats.router)
app.include_router(carbon.router)
app.include_router(alerts.router)


@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """
    Vérifie que l'API et la connexion DB fonctionnent.
    Dépend de `get_db` (abstraction), jamais de l'engine directement,
    ce qui permet de le tester avec une DB de test (voir tests/test_health.py).
    """
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    return {
        "status": "ok" if db_ok else "degraded",
        "database": "connected" if db_ok else "unreachable",
    }
