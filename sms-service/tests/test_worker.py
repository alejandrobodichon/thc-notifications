import json
from datetime import datetime

import httpx
import pytest

from worker import process_message

MESSAGE = {"notification_id": 42, "to": "+5491100000000", "message": "Your code is 1234"}


def make_api(handler, calls: list[httpx.Request]) -> httpx.AsyncClient:
    def spy(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return handler(request)

    return httpx.AsyncClient(
        transport=httpx.MockTransport(spy),
        base_url="http://api.test",
        headers={"X-API-Key": "test-internal-api-key"},
    )


@pytest.mark.anyio
async def test_process_message_reports_sent_to_api():
    calls: list[httpx.Request] = []

    async with make_api(lambda _: httpx.Response(204), calls) as api:
        await process_message(MESSAGE, api)

    assert len(calls) == 1
    request = calls[0]
    assert request.method == "POST"
    assert request.url.path == "/internal/notifications/42/delivery"
    assert request.headers["X-API-Key"] == "test-internal-api-key"
    body = json.loads(request.content)
    assert body["status"] == "sent"
    assert datetime.fromisoformat(body["sent_at"]).tzinfo is not None


@pytest.mark.anyio
@pytest.mark.parametrize("status_code", [401, 404, 500])
async def test_process_message_raises_when_api_rejects(status_code: int):
    calls: list[httpx.Request] = []

    async with make_api(lambda _: httpx.Response(status_code), calls) as api:
        with pytest.raises(httpx.HTTPStatusError):
            await process_message(MESSAGE, api)


@pytest.mark.anyio
async def test_process_message_raises_when_api_is_unreachable():
    def unreachable(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    async with make_api(unreachable, []) as api:
        with pytest.raises(httpx.ConnectError):
            await process_message(MESSAGE, api)
