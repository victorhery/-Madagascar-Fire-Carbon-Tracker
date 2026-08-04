import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    NASA_MAP_KEY: str = os.getenv("NASA_MAP_KEY", "")
    # Emprise BBOX approximative du COFAV (Ouest, Sud, Est, Nord)
    # Ajustable selon vos limites exactes
    COFAV_BBOX: str = "46.5,-22.5,47.8,-20.5"

settings = Settings()