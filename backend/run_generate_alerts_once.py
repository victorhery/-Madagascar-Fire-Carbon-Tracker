"""
Lance manuellement la génération d'alertes basée sur les seuils de densité
de détections FIRMS des dernières 24h.

Usage :
    python run_generate_alerts_once.py
"""
from app.core.database import SessionLocal
from app.jobs.generate_alerts import run_generate_alerts
from app.repositories import SQLAlchemyAlertRepository, SQLAlchemyFireRepository

if __name__ == "__main__":
    db = SessionLocal()
    try:
        fire_repo = SQLAlchemyFireRepository(db)
        alert_repo = SQLAlchemyAlertRepository(db)

        alert = run_generate_alerts(fire_repo, alert_repo)

        if alert is None:
            print("Aucun seuil dépassé -> pas d'alerte créée.")
        else:
            print(f"Alerte créée : niveau={alert.level.value}, région={alert.region}")
            print(alert.message)
    finally:
        db.close()
