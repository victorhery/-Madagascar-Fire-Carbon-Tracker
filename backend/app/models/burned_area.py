from sqlalchemy import Column, Date, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class BurnedArea(Base):
    """
    Une ligne = un résultat d'estimation Google Earth Engine (surface brûlée
    + carbone) pour une région et une période données.

    Calculé beaucoup moins souvent que les détections FIRMS (job quotidien
    ou hebdomadaire, Phase 6), sur les zones où des feux ont été détectés.
    """

    __tablename__ = "burned_areas"

    id = Column(Integer, primary_key=True, index=True)

    region = Column(String, nullable=False, index=True)
    area_hectares = Column(Float, nullable=False)
    carbon_tons_estimate = Column(Float, nullable=False)

    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)

    computed_at = Column(DateTime(timezone=True), server_default=func.now())

    # Lien optionnel vers la détection FIRMS à l'origine du calcul GEE.
    fire_detection_id = Column(
        Integer, ForeignKey("fire_detections.id"), nullable=True
    )
    fire_detection = relationship("FireDetection")

    def __repr__(self) -> str:
        return f"<BurnedArea id={self.id} region={self.region} ha={self.area_hectares}>"