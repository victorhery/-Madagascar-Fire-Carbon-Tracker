from sqlalchemy import Column, Date, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class BurnedArea(Base):
    """
    Une ligne = un résultat d'estimation Google Earth Engine (surface brûlée
    + carbone) pour une région et une période données, produit par UNE
    source précise (`source`: "modis" ou "sentinel2").

    MODIS et Sentinel-2 peuvent chacun produire une estimation pour la même
    région/période -> `source` permet au dashboard de choisir quel résultat
    afficher (voir BurnedAreaRepository.latest_by_region : Sentinel-2 est
    préféré quand disponible, car plus frais).
    """

    __tablename__ = "burned_areas"

    id = Column(Integer, primary_key=True, index=True)

    region = Column(String, nullable=False, index=True)
    area_hectares = Column(Float, nullable=False)
    carbon_tons_estimate = Column(Float, nullable=False)

    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)

    # "modis" (MCD64A1, validé scientifiquement, ~2-3 mois de délai) ou
    # "sentinel2" (dNBR maison, quelques jours de délai, indicatif).
    # Default côté Python ET côté DB pour ne rien casser sur les lignes
    # déjà en base avant cette colonne (voir note de migration).
    source = Column(String, nullable=False, default="modis", server_default="modis")

    computed_at = Column(DateTime(timezone=True), server_default=func.now())

    # Lien optionnel vers la détection FIRMS à l'origine du calcul GEE.
    fire_detection_id = Column(
        Integer, ForeignKey("fire_detections.id"), nullable=True
    )
    fire_detection = relationship("FireDetection")

    def __repr__(self) -> str:
        return f"<BurnedArea id={self.id} region={self.region} ha={self.area_hectares} source={self.source}>"
