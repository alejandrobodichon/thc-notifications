
from datetime import datetime


from alembic.environment import Any
from pydantic import ValidationError

from core.enums import DeliveryStatus
from core.exceptions import InvalidChannelData
from core.strategy.notification_strategy import DeliveryResult, NotificationStrategy
from schemas.notification import PushChannelData
from models.notification import Notification

class PushNotificationStrategy(NotificationStrategy):
    def validate(self, channel_data: dict[str, Any]) -> dict[str, Any]:
        try:
            data = PushChannelData.model_validate(channel_data)
        except ValidationError as e:
            raise InvalidChannelData() from e
        return data.model_dump()
    
    
    async def send_notification(self, notification: Notification) -> DeliveryResult:
        return DeliveryResult(status=DeliveryStatus.SENT, sent_at=datetime.now())
