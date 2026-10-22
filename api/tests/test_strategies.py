"""Unit tests for the channel strategies: no database, no HTTP."""

import pytest

from core.enums import Channel, DeliveryStatus
from core.exceptions import InvalidChannelData
from core.strategy.email_notification_strategy import EmailNotificationStrategy
from core.strategy.push_notification_strategy import PushNotificationStrategy
from core.strategy.sms_notification_strategy import SMS_MAX_LENGTH, SmsNotificationStrategy
from models.notification import Notification
from tests.conftest import FakeSmsPublisher


def make_notification(channel: Channel, channel_data: dict, content: str = "Hello") -> Notification:
    return Notification(
        id=1,
        title="Title",
        content=content,
        channel=channel,
        channel_data=channel_data,
        user_id=1,
    )


class TestSmsStrategy:
    def test_validate_returns_clean_data(self):
        strategy = SmsNotificationStrategy(FakeSmsPublisher())

        assert strategy.validate({"phone_number": "+5491100000000"}) == {
            "phone_number": "+5491100000000"
        }

    @pytest.mark.parametrize("phone", ["5491100000000", "+0123456789", "+54", "+54abc12345"])
    def test_validate_rejects_invalid_phone(self, phone: str):
        strategy = SmsNotificationStrategy(FakeSmsPublisher())

        with pytest.raises(InvalidChannelData):
            strategy.validate({"phone_number": phone})

    @pytest.mark.anyio
    async def test_send_publishes_truncated_message_and_stays_pending(self):
        publisher = FakeSmsPublisher()
        strategy = SmsNotificationStrategy(publisher)
        notification = make_notification(
            Channel.SMS, {"phone_number": "+5491100000000"}, content="a" * 200
        )

        result = await strategy.send_notification(notification)

        assert result.status == DeliveryStatus.PENDING
        assert result.sent_at is None
        assert len(publisher.messages[0]["message"]) == SMS_MAX_LENGTH

    @pytest.mark.anyio
    async def test_send_returns_failed_when_queue_is_down(self):
        publisher = FakeSmsPublisher()
        publisher.fail = True
        strategy = SmsNotificationStrategy(publisher)
        notification = make_notification(Channel.SMS, {"phone_number": "+5491100000000"})

        result = await strategy.send_notification(notification)

        assert result.status == DeliveryStatus.FAILED
        assert result.error


class TestEmailStrategy:
    def test_validate_returns_clean_data(self):
        assert EmailNotificationStrategy().validate({"email": "dest@example.com"}) == {
            "email": "dest@example.com"
        }

    def test_validate_rejects_invalid_email(self):
        with pytest.raises(InvalidChannelData):
            EmailNotificationStrategy().validate({"email": "not-an-email"})

    @pytest.mark.anyio
    async def test_send_marks_as_sent(self):
        notification = make_notification(Channel.EMAIL, {"email": "dest@example.com"})

        result = await EmailNotificationStrategy().send_notification(notification)

        assert result.status == DeliveryStatus.SENT
        assert result.sent_at is not None


class TestPushStrategy:
    def test_validate_returns_clean_data(self):
        token = "t" * 64

        assert PushNotificationStrategy().validate({"device_token": token}) == {
            "device_token": token
        }

    @pytest.mark.parametrize("token", ["short", "t" * 257])
    def test_validate_rejects_invalid_token_length(self, token: str):
        with pytest.raises(InvalidChannelData):
            PushNotificationStrategy().validate({"device_token": token})

    @pytest.mark.anyio
    async def test_send_marks_as_sent(self):
        notification = make_notification(Channel.PUSH, {"device_token": "t" * 64})

        result = await PushNotificationStrategy().send_notification(notification)

        assert result.status == DeliveryStatus.SENT
        assert result.sent_at is not None
