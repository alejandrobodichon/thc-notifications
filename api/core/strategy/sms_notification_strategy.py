import logging
from typing import Any

from pydantic import ValidationError

from clients.sms_queue_publisher import SmsQueuePublisher
from core.enums import DeliveryStatus
from core.exceptions import InvalidChannelData, NotificationNotPersisted, SmsQueueUnavailable
from core.strategy.notification_strategy import NotificationStrategy
from domain.deliveryResult import DeliveryResult
from domain.notification import Notification
from schemas.notification import SmsChannelData

SMS_MAX_LENGTH = 160
logger = logging.getLogger(__name__)


class SmsNotificationStrategy(NotificationStrategy):
    def __init__(self, publisher: SmsQueuePublisher):
        self._publisher = publisher

    def validate(self, channel_data: dict[str, Any]) -> dict[str, Any]:
        try:
            data = SmsChannelData.model_validate(channel_data)
        except ValidationError as e:
            raise InvalidChannelData() from e
        return data.model_dump()

    async def send_notification(self, notification: Notification) -> DeliveryResult:
        if notification.id is None:
            raise NotificationNotPersisted()
        phone = notification.channel_data["phone_number"]
        message = notification.content[:SMS_MAX_LENGTH]
        try:
            await self._publisher.publish(notification.id, phone, message)
        except SmsQueueUnavailable:
            logger.warning(
                "Could not enqueue SMS for notification %s", notification.id, exc_info=True
            )
            return DeliveryResult(status=DeliveryStatus.FAILED, error="SMS queue unavailable")
        logger.info("SMS queued for notification %s", notification.id)
        return DeliveryResult(status=DeliveryStatus.PENDING)
