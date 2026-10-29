from typing import Any

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from core.enums import DeliveryStatus
from domain.deliveryResult import DeliveryResult
from domain.notification import Notification
from models.notification import NotificationModel


def _to_domain(model: NotificationModel) -> Notification:
    return Notification(
        id=model.id,
        title=model.title,
        content=model.content,
        channel=model.channel,
        channel_data=model.channel_data,
        user_id=model.user_id,
        created_at=model.created_at,
        sent_at=model.sent_at,
        delivery_status=model.delivery_status,
    )


def _to_model(notification: Notification) -> NotificationModel:
    return NotificationModel(
        title=notification.title,
        content=notification.content,
        channel=notification.channel,
        channel_data=notification.channel_data,
        user_id=notification.user_id,
        created_at=notification.created_at,
        sent_at=notification.sent_at,
        delivery_status=notification.delivery_status,
    )


class NotificationRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_all_by_user_id(self, user_id: int) -> list[Notification]:
        result = await self._session.execute(
            select(NotificationModel)
            .where(NotificationModel.user_id == user_id)
            .order_by(NotificationModel.created_at.desc())
        )
        return [_to_domain(model) for model in result.scalars()]

    async def get_by_id(self, notification_id: int) -> Notification | None:
        notification_model = await self._session.get(NotificationModel, notification_id)
        if notification_model is None:
            return None
        return _to_domain(notification_model)

    async def get_by_id_for_update(self, notification_id: int) -> Notification | None:
        notification_model = await self._session.get(
            NotificationModel, notification_id, with_for_update=True, populate_existing=True
        )
        if notification_model is None:
            return None
        return _to_domain(notification_model)

    async def insert(self, notification: Notification) -> Notification:
        notification_model = _to_model(notification)
        self._session.add(notification_model)
        await self._session.flush()
        await self._session.refresh(notification_model)
        return _to_domain(notification_model)

    async def commit(self) -> None:
        await self._session.commit()

    async def delete(self, notification_id: int) -> None:
        statement = delete(NotificationModel).where(NotificationModel.id == notification_id)
        await self._session.execute(statement)

    async def update(self, notification_id: int, **changes: Any) -> Notification:
        statement = (
            update(NotificationModel)
            .where(NotificationModel.id == notification_id)
            .values(**changes)
            .returning(NotificationModel)
        )
        result = await self._session.execute(statement)
        return _to_domain(result.scalar_one())

    async def apply_delivery_result(
        self, notification_id: int, result: DeliveryResult
    ) -> Notification | None:
        statement = (
            update(NotificationModel)
            .where(
                NotificationModel.id == notification_id,
                NotificationModel.delivery_status == DeliveryStatus.PENDING,
            )
            .values(delivery_status=result.status, sent_at=result.sent_at)
            .returning(NotificationModel)
        )
        rows = await self._session.execute(statement)
        model = rows.scalar_one_or_none()
        return _to_domain(model) if model is not None else None
