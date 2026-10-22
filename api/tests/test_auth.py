import pytest
from httpx import AsyncClient

from tests.conftest import create_test_user


@pytest.mark.anyio
async def test_login_returns_bearer_token(client: AsyncClient):
    await create_test_user(client)

    response = await client.post(
        "/auth/token",
        data={"username": "testuser", "password": "testpassword123"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]


@pytest.mark.anyio
async def test_login_is_case_insensitive_on_username(client: AsyncClient):
    await create_test_user(client)

    response = await client.post(
        "/auth/token",
        data={"username": "TestUser", "password": "testpassword123"},
    )

    assert response.status_code == 200


@pytest.mark.anyio
async def test_login_wrong_password(client: AsyncClient):
    await create_test_user(client)

    response = await client.post(
        "/auth/token",
        data={"username": "testuser", "password": "wrong-password"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Incorrect username or password."}


@pytest.mark.anyio
async def test_login_unknown_user_gets_same_error_as_wrong_password(client: AsyncClient):
    response = await client.post(
        "/auth/token",
        data={"username": "ghost", "password": "testpassword123"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Incorrect username or password."}


@pytest.mark.anyio
async def test_protected_endpoint_without_token(client: AsyncClient):
    response = await client.post("/notifications", json={})

    assert response.status_code == 401


@pytest.mark.anyio
async def test_protected_endpoint_with_invalid_token(client: AsyncClient):
    response = await client.post(
        "/notifications",
        json={},
        headers={"Authorization": "Bearer not-a-real-token"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials."}
