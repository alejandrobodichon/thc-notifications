
from fastapi import APIRouter, status

from dependencies import CurrentUser, NotificationServiceDep
from schemas.notification import NotificationBase, NotificationCreate

router = APIRouter()


@router.post("", response_model= NotificationCreate, status_code=status.HTTP_201_CREATED)
async def create_notification(
    notification: NotificationBase, 
    current_user: CurrentUser, 
    service: NotificationServiceDep
):
    return await service.create(notification, current_user.id)
