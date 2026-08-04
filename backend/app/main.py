import csv
import io
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings

app = FastAPI(title="Madagascar FireCarbon Tracker API")

# Configuration CORS pour autoriser le frontend Vue.js
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En dev, autorise toutes les origines
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FIRMS_AREA_URL = "https://firms.modaps.eosdis.nasa.gov/api/area/csv"

@app.get("/api/v1/fires/recent")
async def get_recent_fires(day_range: int = 1):
    """
    Récupère les feux récents de la NASA sur la BBOX du COFAV
    et les renvoie au format GeoJSON standard.
    """
    if not settings.NASA_MAP_KEY:
        raise HTTPException(status_code=500, detail="Clé NASA_MAP_KEY manquante dans le .env")

    # URL ciblée sur la BBOX du COFAV avec la clé NASA
    url = f"{FIRMS_AREA_URL}/{settings.NASA_MAP_KEY}/VIIRS_SNPP_NRT/{settings.COFAV_BBOX}/{day_range}"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=10.0)
            response.raise_for_status()

        # Lecture du CSV renvoyé par la NASA
        csv_data = response.text
        reader = csv.DictReader(io.StringIO(csv_data))

        # Construction de la structure GeoJSON
        features = []
        for row in reader:
            try:
                lon = float(row["longitude"])
                lat = float(row["latitude"])
                brightness = float(row.get("bright_ti4", 0))
                confidence = row.get("confidence", "N/A")
                acq_date = row.get("acq_date", "")
                acq_time = row.get("acq_time", "")

                feature = {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [lon, lat]
                    },
                    "properties": {
                        "brightness": brightness,
                        "confidence": confidence,
                        "acq_date": acq_date,
                        "acq_time": acq_time
                    }
                }
                features.append(feature)
            except (ValueError, KeyError):
                continue

        return {
            "type": "FeatureCollection",
            "features": features
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération NASA: {str(e)}")