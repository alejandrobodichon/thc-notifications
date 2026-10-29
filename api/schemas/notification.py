from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from core.enums import Channel, DeliveryStatus


class NotificationBase(BaseModel):
    title: str = Field(min_length=1, max_length=50)
    content: str = Field(min_length=1, max_length=300)
    channel: Channel
    channel_data: dict[str, Any]


class NotificationCreate(NotificationBase):
    pass


class NotificationUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=50)
    content: str | None = Field(default=None, min_length=1, max_length=300)
    channel: Channel | None = Field(default=None)
    channel_data: dict[str, Any] | None = Field(default=None)


class NotificationPublic(NotificationBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    delivery_status: DeliveryStatus
    created_at: datetime
    sent_at: datetime | None


class SmsChannelData(BaseModel):
    phone_number: str = Field(pattern=r"^\+[1-9]\d{7,14}$")


class EmailChannelData(BaseModel):
    email: EmailStr


class PushChannelData(BaseModel):
    device_token: str = Field(min_length=32, max_length=256)


class DeliveryUpdate(BaseModel):
    status: DeliveryStatus
    sent_at: datetime | None = None
    error: str | None = None
