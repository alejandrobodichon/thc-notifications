
from fastapi import APIRouter, status

from dependencies import CurrentUser, NotificationServiceDep
from models.notification import Notification
from schemas.notification import NotificationCreate, NotificationPublic

router = APIRouter()


@router.post("", response_model=NotificationPublic, status_code=status.HTTP_201_CREATED)
async def create_notification(
    notification: NotificationCreate,
    current_user: CurrentUser,
    service: NotificationServiceDep,
) -> Notification:
    return await service.create(notification, current_user.id)
