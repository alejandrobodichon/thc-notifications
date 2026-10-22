from datetime import datetime
from typing import Any

from pydantic import ValidationError

from core.enums import DeliveryStatus
from core.exceptions import InvalidChannelData
from core.strategy.notification_strategy import DeliveryResult, NotificationStrategy
from models.notification import Notification
from schemas.notification import EmailChannelData


class EmailNotificationStrategy(NotificationStrategy):
    def validate(self, channel_data: dict[str, Any]) -> dict[str, Any]:
        try:
            data = EmailChannelData.model_validate(channel_data)
        except ValidationError as e:
            raise InvalidChannelData() from e
        return data.model_dump()

    async def send_notification(self, notification: Notification) -> DeliveryResult:
        # Implement the logic to send an email notification
        # For example, you can use an email sending library or service
        # Here, we'll just print the notification details for demonstration purposes
        print(f"Sending email notification to {notification.channel_data.get('email')}:")
        print(f"Title: {notification.title}")
        print(f"Content: {notification.content}")
        return DeliveryResult(status=DeliveryStatus.SENT, sent_at=datetime.now())
