import datetime

from pydantic import BaseModel, ConfigDict


class BurnedAreaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)  # lit directement les objets SQLAlchemy

    id: int
    region: str
    area_hectares: float
    carbon_tons_estimate: float
    period_start: datetime.date
    period_end: datetime.date
    computed_at: datetime.datetime
    source: str
