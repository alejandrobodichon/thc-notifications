"""List, get, update and delete notifications."""

from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from core.enums import Channel, DeliveryStatus
from domain.deliveryResult import DeliveryResult
from models.notification import NotificationModel
from repositories.notification_repository import NotificationRepository
from tests.conftest import FakeSmsPublisher, create_test_user, login
from tests.test_notifications import EMAIL_PAYLOAD, SMS_PAYLOAD


async def insert_notification(
    db_session: AsyncSession,
    user_id: int,
    *,
    status: DeliveryStatus = DeliveryStatus.SENT,
    channel: Channel = Channel.EMAIL,
    channel_data: dict | None = None,
    title: str = "Title",
    created_at: datetime | None = None,
) -> int:
    model = NotificationModel(
        title=title,
        content="Content",
        channel=channel,
        channel_data=channel_data or {"email": "old@example.com"},
        user_id=user_id,
        delivery_status=status,
        created_at=created_at or datetime.now(UTC),
    )
    db_session.add(model)
    await db_session.flush()
    return model.id


async def other_user_headers(client: AsyncClient) -> tuple[dict, dict[str, str]]:
    other = await create_test_user(client, username="other", email="other@example.com")
    return other, await login(client, username="other")


# ---------- list ----------


@pytest.mark.anyio
async def test_list_returns_only_own_notifications(
    client: AsyncClient, user: dict, auth_headers: dict, db_session: AsyncSession
):
    other, _ = await other_user_headers(client)
    own_id = await insert_notification(db_session, user["id"])
    await insert_notification(db_session, other["id"])

    response = await client.get("/notifications", headers=auth_headers)

    assert response.status_code == 200
    assert [n["id"] for n in response.json()] == [own_id]


@pytest.mark.anyio
async def test_list_is_ordered_newest_first(
    client: AsyncClient, user: dict, auth_headers: dict, db_session: AsyncSession
):
    now = datetime.now(UTC)
    old_id = await insert_notification(
        db_session, user["id"], title="Old", created_at=now - timedelta(hours=1)
    )
    new_id = await insert_notification(db_session, user["id"], title="New", created_at=now)

    response = await client.get("/notifications", headers=auth_headers)

    assert [n["id"] for n in response.json()] == [new_id, old_id]


@pytest.mark.anyio
async def test_list_without_notifications(client: AsyncClient, auth_headers: dict):
    response = await client.get("/notifications", headers=auth_headers)

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.anyio
async def test_list_without_token(client: AsyncClient):
    response = await client.get("/notifications")

    assert response.status_code == 401


# ---------- get ----------


@pytest.mark.anyio
async def test_get_own_notification(
    client: AsyncClient, user: dict, auth_headers: dict, db_session: AsyncSession
):
    notification_id = await insert_notification(db_session, user["id"], title="Mine")

    response = await client.get(f"/notifications/{notification_id}", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["id"] == notification_id
    assert response.json()["title"] == "Mine"


@pytest.mark.anyio
async def test_get_another_users_notification(
    client: AsyncClient, user: dict, db_session: AsyncSession
):
    notification_id = await insert_notification(db_session, user["id"])
    _, other_headers = await other_user_headers(client)

    response = await client.get(f"/notifications/{notification_id}", headers=other_headers)

    assert response.status_code == 403


@pytest.mark.anyio
async def test_get_unknown_notification(client: AsyncClient, auth_headers: dict):
    response = await client.get("/notifications/999999", headers=auth_headers)

    assert response.status_code == 404
    assert response.json() == {"detail": "Notification not found."}


# ---------- delete ----------


@pytest.mark.anyio
async def test_delete_own_notification(
    client: AsyncClient, user: dict, auth_headers: dict, db_session: AsyncSession
):
    notification_id = await insert_notification(db_session, user["id"])

    response = await client.delete(f"/notifications/{notification_id}", headers=auth_headers)

    assert response.status_code == 204
    after = await client.get(f"/notifications/{notification_id}", headers=auth_headers)
    assert after.status_code == 404


@pytest.mark.anyio
async def test_delete_another_users_notification(
    client: AsyncClient, user: dict, auth_headers: dict, db_session: AsyncSession
):
    notification_id = await insert_notification(db_session, user["id"])
    _, other_headers = await other_user_headers(client)

    response = await client.delete(f"/notifications/{notification_id}", headers=other_headers)

    assert response.status_code == 403
    still_there = await client.get(f"/notifications/{notification_id}", headers=auth_headers)
    assert still_there.status_code == 200


@pytest.mark.anyio
async def test_delete_unknown_notification(client: AsyncClient, auth_headers: dict):
    response = await client.delete("/notifications/999999", headers=auth_headers)

    assert response.status_code == 404


@pytest.mark.anyio
async def test_delete_without_token(
    client: AsyncClient, user: dict, auth_headers: dict, db_session: AsyncSession
):
    notification_id = await insert_notification(db_session, user["id"])

    response = await client.delete(f"/notifications/{notification_id}")

    assert response.status_code == 401
    still_there = await client.get(f"/notifications/{notification_id}", headers=auth_headers)
    assert still_there.status_code == 200


# ---------- update (only failed notifications, which are re-sent) ----------


@pytest.mark.anyio
async def test_update_failed_email_is_fixed_and_resent(
    client: AsyncClient, user: dict, auth_headers: dict, db_session: AsyncSession
):
    notification_id = await insert_notification(
        db_session, user["id"], status=DeliveryStatus.FAILED
    )

    response = await client.patch(
        f"/notifications/{notification_id}",
        json={"title": "Fixed", "channel_data": {"email": "new@example.com"}},
        headers=auth_headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Fixed"
    assert body["channel_data"] == {"email": "new@example.com"}
    assert body["delivery_status"] == "sent"
    assert body["sent_at"] is not None


@pytest.mark.anyio
async def test_update_failed_sms_is_requeued_with_new_phone(
    client: AsyncClient, auth_headers: dict, sms_publisher: FakeSmsPublisher
):
    sms_publisher.fail = True
    created = await client.post("/notifications", json=SMS_PAYLOAD, headers=auth_headers)
    assert created.json()["delivery_status"] == "failed"
    sms_publisher.fail = False

    response = await client.patch(
        f"/notifications/{created.json()['id']}",
        json={"channel_data": {"phone_number": "+5491122223333"}},
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["delivery_status"] == "pending"
    assert sms_publisher.messages == [
        {
            "notification_id": created.json()["id"],
            "to": "+5491122223333",
            "message": SMS_PAYLOAD["content"],
        }
    ]


@pytest.mark.anyio
async def test_update_failed_sms_when_queue_is_still_down_stays_failed(
    client: AsyncClient, auth_headers: dict, sms_publisher: FakeSmsPublisher
):
    sms_publisher.fail = True
    created = await client.post("/notifications", json=SMS_PAYLOAD, headers=auth_headers)
    notification_id = created.json()["id"]

    first_retry = await client.patch(
        f"/notifications/{notification_id}", json={"title": "Retry"}, headers=auth_headers
    )
    assert first_retry.json()["delivery_status"] == "failed"

    # Still failed, so it can be edited again.
    sms_publisher.fail = False
    second_retry = await client.patch(
        f"/notifications/{notification_id}", json={"title": "Retry 2"}, headers=auth_headers
    )
    assert second_retry.status_code == 200
    assert second_retry.json()["delivery_status"] == "pending"


@pytest.mark.anyio
async def test_update_can_switch_channel_with_valid_data(
    client: AsyncClient,
    user: dict,
    auth_headers: dict,
    db_session: AsyncSession,
    sms_publisher: FakeSmsPublisher,
):
    notification_id = await insert_notification(
        db_session, user["id"], status=DeliveryStatus.FAILED
    )

    response = await client.patch(
        f"/notifications/{notification_id}",
        json={"channel": "sms", "channel_data": {"phone_number": "+5491100000000"}},
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["channel"] == "sms"
    assert response.json()["delivery_status"] == "pending"
    assert sms_publisher.messages[0]["notification_id"] == notification_id


@pytest.mark.anyio
async def test_update_channel_without_matching_data_is_rejected(
    client: AsyncClient, user: dict, auth_headers: dict, db_session: AsyncSession
):
    notification_id = await insert_notification(
        db_session, user["id"], status=DeliveryStatus.FAILED
    )

    response = await client.patch(
        f"/notifications/{notification_id}", json={"channel": "sms"}, headers=auth_headers
    )

    assert response.status_code == 422
    after = await client.get(f"/notifications/{notification_id}", headers=auth_headers)
    assert after.json()["channel"] == "email"
    assert after.json()["delivery_status"] == "failed"


@pytest.mark.anyio
async def test_update_with_invalid_channel_data_keeps_old_data(
    client: AsyncClient, user: dict, auth_headers: dict, db_session: AsyncSession
):
    notification_id = await insert_notification(
        db_session, user["id"], status=DeliveryStatus.FAILED
    )

    response = await client.patch(
        f"/notifications/{notification_id}",
        json={"channel_data": {"email": "not-an-email"}},
        headers=auth_headers,
    )

    assert response.status_code == 422
    after = await client.get(f"/notifications/{notification_id}", headers=auth_headers)
    assert after.json()["channel_data"] == {"email": "old@example.com"}
    assert after.json()["delivery_status"] == "failed"


@pytest.mark.anyio
async def test_update_sent_notification_is_not_allowed(client: AsyncClient, auth_headers: dict):
    created = await client.post("/notifications", json=EMAIL_PAYLOAD, headers=auth_headers)
    notification_id = created.json()["id"]

    response = await client.patch(
        f"/notifications/{notification_id}", json={"title": "Changed"}, headers=auth_headers
    )

    assert response.status_code == 409
    after = await client.get(f"/notifications/{notification_id}", headers=auth_headers)
    assert after.json()["title"] == EMAIL_PAYLOAD["title"]


@pytest.mark.anyio
async def test_update_pending_notification_is_not_allowed(
    client: AsyncClient, auth_headers: dict, sms_publisher: FakeSmsPublisher
):
    created = await client.post("/notifications", json=SMS_PAYLOAD, headers=auth_headers)
    assert created.json()["delivery_status"] == "pending"

    response = await client.patch(
        f"/notifications/{created.json()['id']}",
        json={"title": "Changed"},
        headers=auth_headers,
    )

    assert response.status_code == 409
    assert len(sms_publisher.messages) == 1  # nothing new was queued


@pytest.mark.anyio
async def test_update_another_users_notification(
    client: AsyncClient, user: dict, auth_headers: dict, db_session: AsyncSession
):
    notification_id = await insert_notification(
        db_session, user["id"], status=DeliveryStatus.FAILED
    )
    _, other_headers = await other_user_headers(client)

    response = await client.patch(
        f"/notifications/{notification_id}", json={"title": "Hacked"}, headers=other_headers
    )

    assert response.status_code == 403
    after = await client.get(f"/notifications/{notification_id}", headers=auth_headers)
    assert after.json()["title"] == "Title"


@pytest.mark.anyio
async def test_update_unknown_notification(client: AsyncClient, auth_headers: dict):
    response = await client.patch(
        "/notifications/999999", json={"title": "x"}, headers=auth_headers
    )

    assert response.status_code == 404


@pytest.mark.anyio
async def test_update_without_token(client: AsyncClient):
    response = await client.patch("/notifications/1", json={"title": "x"})

    assert response.status_code == 401


# ---------- repository ----------


@pytest.mark.anyio
async def test_apply_delivery_result_does_not_overwrite_final_state(
    client: AsyncClient, user: dict, db_session: AsyncSession
):
    notification_id = await insert_notification(db_session, user["id"], status=DeliveryStatus.SENT)
    repo = NotificationRepository(db_session)

    updated = await repo.apply_delivery_result(
        notification_id, DeliveryResult(status=DeliveryStatus.PENDING)
    )

    assert updated is None
    current = await repo.get_by_id(notification_id)
    assert current is not None
    assert current.delivery_status == DeliveryStatus.SENT
