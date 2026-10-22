import json

from core.exceptions import SmsQueueUnavailable


class SmsQueuePublisher:
    def __init__(self, sqs_client, queue_url: str) -> None:
        self._sqs = sqs_client
        self._queue_url = queue_url

    async def publish(self, notification_id: int, to: str, message: str) -> None:
        try:
            await self._sqs.send_message(
                QueueUrl=self._queue_url,
                MessageBody=json.dumps(
                    {"notification_id": notification_id, "to": to, "message": message}
                ),
            )
        except Exception as e:
            raise SmsQueueUnavailable() from e
