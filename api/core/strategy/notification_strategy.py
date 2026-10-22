from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

from alembic.environment import Any

from core.enums import DeliveryStatus
from models.notification import Notification


@dataclass(frozen=True)
class DeliveryResult:
    status: DeliveryStatus
    sent_at: datetime | None = None
    error: str | None = None


class NotificationStrategy(ABC):
    @abstractmethod
    def validate(self, channel_data: dict[str, Any]) -> dict[str, Any]: ...

    @abstractmethod
    async def send_notification(self, notification: Notification) -> DeliveryResult: ...
