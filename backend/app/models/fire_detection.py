from sqlalchemy import Column, Date, DateTime, Float, Integer, String, UniqueConstraint, func

from app.core.database import Base


class FireDetection(Base):
    """
    Une ligne = une détection de feu remontée par NASA FIRMS.

    Contrainte d'unicité : FIRMS est interrogé toutes les 3-4h avec un
    day_range qui se chevauche (pour ne rater aucune détection), donc la
    même détection peut apparaître plusieurs fois dans les réponses brutes.
    (latitude, longitude, acq_date, acq_time, satellite) identifie une
    détection unique : toute tentative de doublon lèvera une IntegrityError,
    ce que le job de polling (Phase 4) devra gérer explicitement.
    """

    __tablename__ = "fire_detections"
    __table_args__ = (
        UniqueConstraint(
            "latitude", "longitude", "acq_date", "acq_time", "satellite",
            name="uq_fire_detection_dedup",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)

    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)

    brightness = Column(Float, nullable=True)
    confidence = Column(String, nullable=True)
    frp = Column(Float, nullable=True)  # Fire Radiative Power (MW)

    acq_date = Column(Date, nullable=False)
    acq_time = Column(String, nullable=False)  # format brut FIRMS "HHMM"

    satellite = Column(String, nullable=False, default="VIIRS_SNPP_NRT")

    # Renseigné plus tard par un job de rapprochement géographique
    # (pas fourni directement par FIRMS) — nullable pour l'instant.
    region = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self) -> str:
        return f"<FireDetection id={self.id} lat={self.latitude} lon={self.longitude} date={self.acq_date}>"