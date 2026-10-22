import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.enums import DeliveryStatus
from models.notification import Notification
from tests.test_notifications import SMS_PAYLOAD

API_KEY_HEADER = {"X-API-Key": settings.internal_api_key}
SENT_AT = "2026-10-21T12:00:00Z"


async def create_pending_sms(client: AsyncClient, auth_headers: dict) -> int:
    response = await client.post("/notifications", json=SMS_PAYLOAD, headers=auth_headers)
    assert response.json()["delivery_status"] == "pending"
    return response.json()["id"]


async def get_notification(db_session: AsyncSession, notification_id: int) -> Notification:
    notification = await db_session.get(Notification, notification_id, populate_existing=True)
    assert notification is not None
    return notification


@pytest.mark.anyio
async def test_delivery_update_marks_pending_as_sent(
    client: AsyncClient, auth_headers: dict, db_session: AsyncSession
):
    notification_id = await create_pending_sms(client, auth_headers)

    response = await client.post(
        f"/internal/notifications/{notification_id}/delivery",
        json={"status": "sent", "sent_at": SENT_AT},
        headers=API_KEY_HEADER,
    )

    assert response.status_code == 204
    notification = await get_notification(db_session, notification_id)
    assert notification.delivery_status == DeliveryStatus.SENT
    assert notification.sent_at is not None


@pytest.mark.anyio
async def test_delivery_update_can_mark_as_failed(
    client: AsyncClient, auth_headers: dict, db_session: AsyncSession
):
    notification_id = await create_pending_sms(client, auth_headers)

    response = await client.post(
        f"/internal/notifications/{notification_id}/delivery",
        json={"status": "failed", "error": "Provider rejected the number"},
        headers=API_KEY_HEADER,
    )

    assert response.status_code == 204
    notification = await get_notification(db_session, notification_id)
    assert notification.delivery_status == DeliveryStatus.FAILED
    assert notification.sent_at is None


@pytest.mark.anyio
async def test_delivery_update_is_idempotent(
    client: AsyncClient, auth_headers: dict, db_session: AsyncSession
):
    notification_id = await create_pending_sms(client, auth_headers)
    url = f"/internal/notifications/{notification_id}/delivery"
    await client.post(url, json={"status": "sent", "sent_at": SENT_AT}, headers=API_KEY_HEADER)

    # A redelivered queue message must not overwrite the final state.
    response = await client.post(url, json={"status": "failed"}, headers=API_KEY_HEADER)

    assert response.status_code == 204
    notification = await get_notification(db_session, notification_id)
    assert notification.delivery_status == DeliveryStatus.SENT


@pytest.mark.anyio
async def test_delivery_update_unknown_notification(client: AsyncClient):
    response = await client.post(
        "/internal/notifications/999999/delivery",
        json={"status": "sent", "sent_at": SENT_AT},
        headers=API_KEY_HEADER,
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Notification not found."}


@pytest.mark.anyio
async def test_delivery_update_with_wrong_api_key(
    client: AsyncClient, auth_headers: dict, db_session: AsyncSession
):
    notification_id = await create_pending_sms(client, auth_headers)

    response = await client.post(
        f"/internal/notifications/{notification_id}/delivery",
        json={"status": "sent", "sent_at": SENT_AT},
        headers={"X-API-Key": "wrong-key"},
    )

    assert response.status_code == 401
    notification = await get_notification(db_session, notification_id)
    assert notification.delivery_status == DeliveryStatus.PENDING


@pytest.mark.anyio
async def test_delivery_update_without_api_key(client: AsyncClient):
    response = await client.post(
        "/internal/notifications/1/delivery",
        json={"status": "sent", "sent_at": SENT_AT},
    )

    assert response.status_code == 422


@pytest.mark.anyio
async def test_delivery_update_does_not_accept_user_token(client: AsyncClient, auth_headers: dict):
    notification_id = await create_pending_sms(client, auth_headers)

    response = await client.post(
        f"/internal/notifications/{notification_id}/delivery",
        json={"status": "sent", "sent_at": SENT_AT},
        headers=auth_headers,
    )

    assert response.status_code == 422
