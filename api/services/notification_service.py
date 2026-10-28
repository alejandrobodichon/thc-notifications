
from core.enums import Channel, DeliveryStatus
from core.exceptions import (
    NotAuthorized,
    NotificationNotEditable,
    NotificationNotFound,
    NotificationNotPersisted,
)
from core.strategy.notification_strategy import NotificationStrategy
from domain.notification import  Notification
from domain.deliveryResult import DeliveryResult
from repositories.notification_repository import NotificationRepository
from schemas.notification import NotificationBase, NotificationUpdate


class NotificationService:
    def __init__(
        self,
        notification_repo: NotificationRepository,
        registry: dict[Channel, NotificationStrategy],
    ):
        self._repo = notification_repo
        self._registry = registry

    async def create(self, notification_create: NotificationBase, user_id: int) -> Notification:
        strategy = self._registry[notification_create.channel]
        channel_data = strategy.validate(notification_create.channel_data)

        notification = Notification(
            content=notification_create.content,
            user_id=user_id,
            title=notification_create.title,
            channel=notification_create.channel,
            channel_data=channel_data,
        )

        saved_notification = await self._repo.insert(notification)
        await self._repo.commit()

        sended_notification = await self._send_notification(strategy, saved_notification)

        return sended_notification

    async def _send_notification(
            self, 
            strategy: NotificationStrategy, 
            notification: Notification
    ) -> Notification:
        send_status = await strategy.send_notification(notification)
        return await self._update_status(notification, send_status)

    async def get(self, notification_id: int, user_id: int) -> Notification:
        notification = await self._repo.get_by_id(notification_id)

        if notification is None:
            raise NotificationNotFound()

        if notification.user_id != user_id:
            raise NotAuthorized()

        return notification

    async def _update_status(
            self, 
            notification: Notification, 
            delivery_update: DeliveryResult
    ) -> Notification:
        if notification.id is None:
            raise NotificationNotPersisted()
        updated = await self._repo.apply_delivery_result(notification.id, delivery_update)
        if updated is not None:
            return updated
        current = await self._repo.get_by_id(notification.id)
        assert current is not None
        return current
    

    async def update_delivery(self, notification_id: int, data: DeliveryResult) -> None:
        notification = await self._repo.get_by_id(notification_id)
        if notification is None:
            raise NotificationNotFound()
        if notification.delivery_status != DeliveryStatus.PENDING:
            return
        await self._update_status(notification, data)


    async def list_by_user(self, user_id: int) -> list[Notification]:
        return await self._repo.get_all_by_user_id(user_id)


    async def delete(self, notification_id: int, user_id: int) -> None:
        notification = await self._repo.get_by_id(notification_id)
        if notification is None:
            raise NotificationNotFound()
        if notification.user_id != user_id:
            raise NotAuthorized()
        await self._repo.delete(notification_id)
        await self._repo.commit()

    async def update(
            self, notification_id: int, data: NotificationUpdate, user_id: int
    ) -> Notification:
        notification = await self._repo.get_by_id_for_update(notification_id)
        if notification is None:
            raise NotificationNotFound()
        if notification.user_id != user_id:
            raise NotAuthorized()
        if notification.delivery_status != DeliveryStatus.FAILED:
            raise NotificationNotEditable()

        changes = data.model_dump(exclude_unset=True, exclude_none=True)
        
        channel = changes.get("channel", notification.channel)
        strategy = self._registry[channel]

        channel_data = changes.get("channel_data", notification.channel_data)
        validated_channel_data = strategy.validate(channel_data)

        changes["channel_data"] = validated_channel_data

        changes["delivery_status"] = DeliveryStatus.PENDING
        changes["sent_at"] = None

        updated_notification = await self._repo.update(notification_id, **changes)
        await self._repo.commit()

        sended_notification = await self._send_notification(strategy, updated_notification)

        return sended_notification

