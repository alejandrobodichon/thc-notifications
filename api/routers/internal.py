from fastapi import APIRouter

from dependencies import InternalApiKeyDep, NotificationServiceDep
from schemas.notification import DeliveryUpdate

router = APIRouter()


@router.post("/notifications/{notification_id}/delivery", status_code=204)
async def update_delivery(
    notification_id: int,
    data: DeliveryUpdate,
    _: InternalApiKeyDep,
    service: NotificationServiceDep,
) -> None:
    await service.update_delivery(notification_id, data)
