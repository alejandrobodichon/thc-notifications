import httpx

from core.exceptions import SmsGatewayUnavailable


class SmsClient:
    def __init__(self, http: httpx.AsyncClient):
        self._http = http

    async def send(self, to: str, message: str) -> str:
        try:
            response = await self._http.post("/sms", json={"to": to, "message": message})
            response.raise_for_status()
        except httpx.HTTPError as e:
            raise  SmsGatewayUnavailable() from e
        return response.json()["message_id"]
