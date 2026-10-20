from enums import DeliveryStatus
from pydantic import BaseModel, Field


class SmsResponse(BaseModel):
    status: DeliveryStatus
    error: str | None = Field(default=None, min_length=1, max_length=300)

class SmsRequest(BaseModel):
    phone: int = Field(pattern=r"^\+[1-9]\d{7,14}$")
    text: str = Field( min_length=1, max_length=160)