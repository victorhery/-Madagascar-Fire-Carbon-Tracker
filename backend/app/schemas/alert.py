import datetime

from pydantic import BaseModel, ConfigDict

from app.models import AlertLevel


class AlertOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    region: str
    level: AlertLevel
    message: str
    triggered_at: datetime.datetime
    resolved: bool
