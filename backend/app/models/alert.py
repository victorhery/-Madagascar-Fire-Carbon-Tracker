import enum

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class AlertLevel(str, enum.Enum):
    """Enum Python -> empêche d'insérer une valeur de niveau invalide en base."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Alert(Base):
    """
    Une ligne = une alerte générée pour une zone jugée critique
    (ex : forte densité de détections FIRMS sur une courte période).
    Alimente le KPI "alertes du jour" du dashboard.
    """

    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)

    region = Column(String, nullable=False, index=True)
    level = Column(
        Enum(AlertLevel, create_constraint=True, validate_strings=True),
        nullable=False,
        default=AlertLevel.LOW,
    )
    message = Column(String, nullable=False)

    triggered_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved = Column(Boolean, nullable=False, default=False)

    fire_detection_id = Column(
        Integer, ForeignKey("fire_detections.id"), nullable=True
    )
    fire_detection = relationship("FireDetection")

    def __repr__(self) -> str:
        return f"<Alert id={self.id} region={self.region} level={self.level}>"