from datetime import datetime
from typing import Any

from pydantic import ValidationError

from core.enums import DeliveryStatus
from core.exceptions import InvalidChannelData
from core.strategy.notification_strategy import NotificationStrategy
from domain.deliveryResult import DeliveryResult
from domain.notification import Notification
from schemas.notification import EmailChannelData


class EmailNotificationStrategy(NotificationStrategy):
    def validate(self, channel_data: dict[str, Any]) -> dict[str, Any]:
        try:
            data = EmailChannelData.model_validate(channel_data)
        except ValidationError as e:
            raise InvalidChannelData() from e
        return data.model_dump()

    async def send_notification(self, notification: Notification) -> DeliveryResult:
        print(f"Sending email notification to {notification.channel_data.get('email')}:")
        print(f"Title: {notification.title}")
        print(f"Content: {notification.content}")
        return DeliveryResult(status=DeliveryStatus.SENT, sent_at=datetime.now())
