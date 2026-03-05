from pydantic import BaseModel


class Alert(BaseModel):
    id: str
    source: str
    service: str
    environment: str
    metric: str
    value: str
    threshold: str
    message: str
    timestamp: str
