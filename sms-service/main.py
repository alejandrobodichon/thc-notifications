from contextlib import asynccontextmanager

import httpx
from enums import DeliveryStatus
from fastapi import FastAPI, Request, status
from schema.sms_response import SmsRequest, SmsResponse


@asynccontextmanager
async def lifespan(_app: FastAPI):
    async with httpx.AsyncClient() as http_client:
        app.state.http_client = http_client
        yield

app = FastAPI(lifespan=lifespan)

@app.post("/sms", response_model=SmsResponse, status_code=status.HTTP_202_ACCEPTED)
async def send_sms(sms_request: SmsRequest):
    # Simulate sending SMS
    print(f"Sending SMS to {sms_request.phone}: {sms_request.text}")
    # In a real implementation, you would integrate with an SMS gateway here
    return SmsResponse(status=DeliveryStatus.SENT)
    

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)

    response.headers["X-Frame-Options"] = "SAMEORIGIN"

    response.headers["X-Content-Type-Options"] = "nosniff"

    if "Referrer-Policy" not in response.headers:
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    if request.url.hostname not in ("localhost", "127.0.0.1"):
        response.headers["Strict-Transport-Security"] = (
            "max-age=63072000; includeSubDomains"
        )

    return response
