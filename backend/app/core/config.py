import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """
    Configuration centralisée de l'application.
    Responsabilité unique (S de SOLID) : exposer les variables d'environnement
    et les constantes de config. Ne contient AUCUNE logique métier.
    """

    # --- NASA FIRMS (existant) ---
    NASA_MAP_KEY: str = os.getenv("NASA_MAP_KEY", "")
    # Emprise BBOX approximative du COFAV (Ouest, Sud, Est, Nord)
    COFAV_BBOX: str = "46.5,-22.5,47.8,-20.5"

    # --- Base de données PostgreSQL (Phase 0) ---
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://postgres:postgres@localhost:5432/firecarbon",
    )

    # --- Google Earth Engine ---
    # Mode "compte de service" (Phase 6, prévu pour la production/ONG) :
    # GEE_SERVICE_ACCOUNT_JSON doit être renseigné.
    # Mode "authentification personnelle" (dev local, sans clé JSON) :
    # laisser GEE_SERVICE_ACCOUNT_JSON vide, renseigner seulement GEE_PROJECT_ID,
    # et avoir lancé `earthengine authenticate` une fois dans ce venv.
    GEE_SERVICE_ACCOUNT_JSON: str = os.getenv("GEE_SERVICE_ACCOUNT_JSON", "")
    GEE_PROJECT_ID: str = os.getenv("GEE_PROJECT_ID", "")


settings = Settings()
