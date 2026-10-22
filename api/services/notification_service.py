from core.enums import Channel, DeliveryStatus
from core.exceptions import (
    NotificationNotFound,
)
from core.strategy.notification_strategy import NotificationStrategy
from models.notification import Notification
from repositories.notification_repository import NotificationRepository
from schemas.notification import DeliveryUpdate, NotificationBase


class NotificationService:
    def __init__(
        self, 
        notification_repo: NotificationRepository,
        registry: dict[Channel, NotificationStrategy]
    ):
        self._repo = notification_repo
        self._registry = registry

    async def create(self, notification_create: NotificationBase, user_id: int) -> Notification:
        strategy = self._registry[notification_create.channel]
        channel_data = strategy.validate(notification_create.channel_data)

        notification = Notification(
            content = notification_create.content,
            user_id = user_id,
            title = notification_create.title,
            channel = notification_create.channel,
            channel_data = channel_data
        )
        
        saved_notification = await self._repo.save(notification)
        await self._repo.commit()      


        send_status = await strategy.send_notification(saved_notification)

        saved_notification.delivery_status = send_status.status
        saved_notification.sent_at = send_status.sent_at

        await self._repo.save(saved_notification)

        return saved_notification



    async def get(self, notification_id: int) -> Notification:
        notification = await self._repo.get_by_id(notification_id)

        if notification is None:
            raise NotificationNotFound()

        return notification

    async def update_delivery(self, notification_id: int, data: DeliveryUpdate) -> None:
        notification = await self._repo.get_by_id(notification_id)
        if notification is None:
            raise NotificationNotFound()
        if notification.delivery_status != DeliveryStatus.PENDING:
            return 
        notification.delivery_status = data.status
        notification.sent_at = data.sent_at
        await self._repo.save(notification)