from app.core.database import Base, engine

# L'import ci-dessous est nécessaire même si "inutilisé" en apparence :
# il force Python à enregistrer les 3 modèles sur Base.metadata avant
# l'appel à create_all(). Sans cet import, aucune table ne serait créée.
from app.models import FireDetection, BurnedArea, Alert  # noqa: F401


def init_db() -> None:
    """
    Crée les tables manquantes dans la base configurée (DATABASE_URL).
    Ne touche pas aux tables existantes (pas de migration, pas de suppression).
    À lancer manuellement via `python create_tables.py` après tout ajout
    ou modification de modèle.
    """
    Base.metadata.create_all(bind=engine)