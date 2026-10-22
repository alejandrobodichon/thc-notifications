from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.notification import Notification


class NotificationRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_all_by_user_id(self, user_id: int) -> list[Notification]:
        result = await self._session.execute(
            select(Notification).where(Notification.user_id == user_id)
        )
        return list(result.scalars())

    async def get_by_id(self, notification_id: int) -> Notification | None:
        return await self._session.get(Notification, notification_id)

    async def save(self, notification: Notification) -> Notification:
        self._session.add(notification)
        await self._session.flush()
        await self._session.refresh(notification)
        return notification

    async def commit(self) -> None:
        await self._session.commit()
