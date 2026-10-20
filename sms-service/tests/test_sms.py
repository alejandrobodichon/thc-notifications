from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_send_sms_returns_202_with_message_id() -> None:
    response = client.post("/sms", json={"phone": "+5491100000000", "text": "Hola"})

    assert response.status_code == 202
    assert response.json()["status"] == "sent"
    assert "message_id" in response.json()