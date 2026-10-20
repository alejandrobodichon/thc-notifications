
from datetime import UTC, datetime
from typing import Any

import logging
from pydantic import ValidationError

from clients.sms_client import SmsClient
from core.enums import DeliveryStatus
from core.exceptions import InvalidChannelData, SmsGatewayUnavailable
from core.strategy.notification_strategy import DeliveryResult, NotificationStrategy
from models.notification import Notification
from schemas.notification import SmsChannelData

SMS_MAX_LENGTH = 160
logger = logging.getLogger(__name__)

class SmsNotificationStrategy(NotificationStrategy):
    def __init__(self, client: SmsClient):
        self._client = client

    def validate(self, channel_data: dict[str, Any]) -> dict[str, Any]:
        try:
            data = SmsChannelData.model_validate(channel_data)
        except ValidationError as e:
            raise InvalidChannelData() from e
        return data.model_dump()

    async def send_notification(self, notification: Notification) -> DeliveryResult:
        phone = notification.channel_data["phone_number"]
        message = notification.content[:SMS_MAX_LENGTH]
        try:
            message_id = await self._client.send(to=phone, message=message)
        except SmsGatewayUnavailable as e:
            logger.warning("SMS gateway unavailable for notification %s error: %s", 
                           notification.id, str(e))
            return DeliveryResult(status=DeliveryStatus.FAILED, error="SMS gateway unavailable")
        logger.info("SMS %s sent for notification %s", message_id, notification.id)
        return DeliveryResult(status=DeliveryStatus.SENT, sent_at=datetime.now(UTC))
