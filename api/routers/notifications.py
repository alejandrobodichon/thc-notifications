from fastapi import APIRouter, status

from dependencies import CurrentUser, NotificationServiceDep
from domain.notification import Notification
from schemas.notification import NotificationCreate, NotificationPublic, NotificationUpdate

router = APIRouter()


@router.post("", response_model=NotificationPublic, status_code=status.HTTP_201_CREATED)
async def create_notification(
    notification: NotificationCreate,
    current_user: CurrentUser,
    service: NotificationServiceDep,
) -> Notification:
    return await service.create(notification, current_user.id)

@router.get("/{notification_id}", response_model=NotificationPublic)
async def get_notification(
    notification_id: int,
    current_user: CurrentUser,
    service: NotificationServiceDep,
) -> Notification:
    return await service.get(notification_id, current_user.id)

@router.get("", response_model=list[NotificationPublic])
async def list_notifications(
    current_user: CurrentUser,
    service: NotificationServiceDep,
) -> list[Notification]:
    return await service.list_by_user(current_user.id)

@router.delete("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_notification(
    notification_id: int,
    current_user: CurrentUser,
    service: NotificationServiceDep,
) -> None:
    return await service.delete(notification_id, current_user.id)   

@router.patch("/{notification_id}", response_model=NotificationPublic)
async def update_notification(
    notification_id: int,
    data: NotificationUpdate,
    current_user: CurrentUser,
    service: NotificationServiceDep,
) -> Notification:
    return await service.update(notification_id, data, current_user.id)

