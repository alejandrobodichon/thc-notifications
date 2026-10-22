import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.notification import Notification
from tests.conftest import FakeSmsPublisher

EMAIL_PAYLOAD = {
    "title": "Welcome",
    "content": "Thanks for signing up",
    "channel": "email",
    "channel_data": {"email": "dest@example.com"},
}
SMS_PAYLOAD = {
    "title": "Code",
    "content": "Your code is 1234",
    "channel": "sms",
    "channel_data": {"phone_number": "+5491100000000"},
}
PUSH_PAYLOAD = {
    "title": "Ping",
    "content": "You have a new message",
    "channel": "push",
    "channel_data": {"device_token": "a" * 64},
}


async def count_notifications(db_session: AsyncSession) -> int:
    return await db_session.scalar(select(func.count()).select_from(Notification)) or 0


@pytest.mark.anyio
@pytest.mark.parametrize("payload", [EMAIL_PAYLOAD, PUSH_PAYLOAD], ids=["email", "push"])
async def test_create_synchronous_channel_is_sent(
    client: AsyncClient, auth_headers: dict, payload: dict
):
    response = await client.post("/notifications", json=payload, headers=auth_headers)

    assert response.status_code == 201
    body = response.json()
    assert body["id"]
    assert body["channel"] == payload["channel"]
    assert body["delivery_status"] == "sent"
    assert body["sent_at"] is not None


@pytest.mark.anyio
async def test_create_sms_is_queued_as_pending(
    client: AsyncClient, auth_headers: dict, sms_publisher: FakeSmsPublisher
):
    response = await client.post("/notifications", json=SMS_PAYLOAD, headers=auth_headers)

    assert response.status_code == 201
    body = response.json()
    assert body["delivery_status"] == "pending"
    assert body["sent_at"] is None
    assert sms_publisher.messages == [
        {
            "notification_id": body["id"],
            "to": "+5491100000000",
            "message": "Your code is 1234",
        }
    ]


@pytest.mark.anyio
async def test_create_sms_truncates_message_to_160_chars(
    client: AsyncClient, auth_headers: dict, sms_publisher: FakeSmsPublisher
):
    payload = {**SMS_PAYLOAD, "content": "x" * 300}

    response = await client.post("/notifications", json=payload, headers=auth_headers)

    assert response.status_code == 201
    assert response.json()["content"] == "x" * 300
    assert sms_publisher.messages[0]["message"] == "x" * 160


@pytest.mark.anyio
async def test_create_sms_when_queue_is_down_is_saved_as_failed(
    client: AsyncClient,
    auth_headers: dict,
    sms_publisher: FakeSmsPublisher,
    db_session: AsyncSession,
):
    sms_publisher.fail = True

    response = await client.post("/notifications", json=SMS_PAYLOAD, headers=auth_headers)

    assert response.status_code == 201
    assert response.json()["delivery_status"] == "failed"
    assert await count_notifications(db_session) == 1


@pytest.mark.anyio
async def test_create_stores_owner_from_token(
    client: AsyncClient, auth_headers: dict, user: dict, db_session: AsyncSession
):
    response = await client.post("/notifications", json=EMAIL_PAYLOAD, headers=auth_headers)

    notification = await db_session.get(Notification, response.json()["id"])
    assert notification is not None
    assert notification.user_id == user["id"]


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("channel", "channel_data"),
    [
        ("email", {"email": "not-an-email"}),
        ("email", {}),
        ("sms", {"phone_number": "12345"}),
        ("sms", {"phone": "+5491100000000"}),
        ("push", {"device_token": "too-short"}),
    ],
    ids=["email-format", "email-missing", "sms-format", "sms-wrong-key", "push-short-token"],
)
async def test_create_with_invalid_channel_data(
    client: AsyncClient,
    auth_headers: dict,
    sms_publisher: FakeSmsPublisher,
    db_session: AsyncSession,
    channel: str,
    channel_data: dict,
):
    payload = {**EMAIL_PAYLOAD, "channel": channel, "channel_data": channel_data}

    response = await client.post("/notifications", json=payload, headers=auth_headers)

    assert response.status_code == 422
    assert response.json() == {"detail": "Invalid channel data."}
    assert await count_notifications(db_session) == 0
    assert sms_publisher.messages == []


@pytest.mark.anyio
async def test_create_with_unknown_channel(client: AsyncClient, auth_headers: dict):
    payload = {**EMAIL_PAYLOAD, "channel": "fax"}

    response = await client.post("/notifications", json=payload, headers=auth_headers)

    assert response.status_code == 422
    assert "channel" in response.text


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("field", "value"),
    [("title", ""), ("title", "t" * 51), ("content", ""), ("content", "c" * 301)],
    ids=["empty-title", "long-title", "empty-content", "long-content"],
)
async def test_create_with_invalid_message(
    client: AsyncClient, auth_headers: dict, field: str, value: str
):
    payload = {**EMAIL_PAYLOAD, field: value}

    response = await client.post("/notifications", json=payload, headers=auth_headers)

    assert response.status_code == 422
    assert field in response.text


@pytest.mark.anyio
async def test_create_without_token(client: AsyncClient, db_session: AsyncSession):
    response = await client.post("/notifications", json=EMAIL_PAYLOAD)

    assert response.status_code == 401
    assert await count_notifications(db_session) == 0
