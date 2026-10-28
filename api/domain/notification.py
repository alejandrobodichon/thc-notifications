from dataclasses import dataclass
from datetime import datetime

from alembic.environment import Any

from core.enums import Channel, DeliveryStatus


@dataclass(frozen=True)
class Notification:
    title: str
    content: str
    user_id: int
    channel: Channel
    channel_data: dict[str, Any]

    id: int | None = None
    delivery_status: DeliveryStatus = DeliveryStatus.PENDING
    created_at: datetime | None = None
    sent_at: datetime | None = None    

