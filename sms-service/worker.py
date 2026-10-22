import asyncio
import json
import logging
from datetime import UTC, datetime

import aioboto3
import httpx

from config import settings

logger = logging.getLogger("sms_worker")



async def process_message(body: dict, api: httpx.AsyncClient) -> None:
    logger.info("SMS sent to %s: %s", body["to"], body["message"])
    response = await api.post(
        f"/internal/notifications/{body['notification_id']}/delivery",
        json={"status": "sent", "sent_at": datetime.now(UTC).isoformat()},
    )
    response.raise_for_status()


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    session = aioboto3.Session()
    async with (
        session.client(
            "sqs",
            endpoint_url=settings.sqs_endpoint_url,
            region_name=settings.aws_region,
            aws_access_key_id="local",
            aws_secret_access_key="local",
        ) as sqs,
        httpx.AsyncClient(
            base_url=settings.api_url, 
            headers={"X-API-Key": settings.internal_api_key.get_secret_value()}, 
            timeout=5
        ) as api,
    ):
        queue_url = (await sqs.get_queue_url(QueueName=settings.sms_queue_name))["QueueUrl"]
        logger.info("Worker listening on %s", queue_url)

        while True:
            response = await sqs.receive_message(
                QueueUrl=queue_url, MaxNumberOfMessages=10, WaitTimeSeconds=20
            )
            for msg in response.get("Messages", []):
                try:
                    await process_message(json.loads(msg["Body"]), api)
                except Exception:
                    logger.exception("Failed to process message %s", msg["MessageId"])
                    continue  # no se borra → se reintenta → DLQ
                await sqs.delete_message(QueueUrl=queue_url, ReceiptHandle=msg["ReceiptHandle"])


if __name__ == "__main__":
    asyncio.run(main())