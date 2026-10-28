from abc import ABC, abstractmethod

from alembic.environment import Any

from domain.deliveryResult import DeliveryResult
from domain.notification import Notification


class NotificationStrategy(ABC):
    @abstractmethod
    def validate(self, channel_data: dict[str, Any]) -> dict[str, Any]: ...

    @abstractmethod
    async def send_notification(self, notification: Notification) -> DeliveryResult: ...
