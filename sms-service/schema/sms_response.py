from pydantic import BaseModel, Field

from enums import DeliveryStatus


class SmsResponse(BaseModel):
    message_id: str = Field(min_length=1, max_length=100)
    status: DeliveryStatus
    error: str | None = Field(default=None, min_length=1, max_length=300)

class SmsRequest(BaseModel):
    phone: str = Field(pattern=r"^\+[1-9]\d{7,14}$")
    text: str = Field( min_length=1, max_length=160)