import pytest
from httpx import AsyncClient

from tests.conftest import create_test_user, login


@pytest.mark.anyio
async def test_create_user_ok(client: AsyncClient):
    response = await client.post(
        "/users",
        json={"username": "testuser", "email": "test@example.com", "password": "testpassword123"},
    )

    assert response.status_code == 201


@pytest.mark.anyio
async def test_create_user_validation_error(client: AsyncClient):
    response = await client.post(
        "/users",
        json={
            "username": "testuser",
        },
    )

    assert response.status_code == 422
    assert "email" in response.text
    assert "password" in response.text


@pytest.mark.anyio
async def test_create_user_email_already_exist(client: AsyncClient):
    await create_test_user(client)

    response = await client.post(
        "/users",
        json={"username": "testuser", "email": "test@example.com", "password": "testpassword123"},
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "Email already exists."}


@pytest.mark.anyio
async def test_create_user_username_already_exist(client: AsyncClient):
    await create_test_user(client)

    response = await client.post(
        "/users",
        json={"username": "testuser", "email": "test2@example.com", "password": "testpassword123"},
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "Username already exists."}


@pytest.mark.anyio
async def test_get_user_that_already_exist(client: AsyncClient):
    user = await create_test_user(client)

    response = await client.get("/users")

    assert response.status_code == 200
    assert response.json() == [
        {"id": user["id"], "username": "testuser", "email": "test@example.com"}
    ]


@pytest.mark.anyio
async def test_get_user_without_users(client: AsyncClient):

    response = await client.get("/users")

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.anyio
async def test_get_user_by_id_not_exist(client: AsyncClient):
    user_id = 1
    response = await client.get(f"/users/{user_id}")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "User not found.",
    }


@pytest.mark.anyio
async def test_get_user_by_id_exist(client: AsyncClient):
    user = await create_test_user(client)
    response = await client.get(f"/users/{user['id']}")

    assert response.status_code == 200
    assert response.json() == {
        "id": user["id"],
        "username": "testuser",
        "email": "test@example.com",
    }


async def create_other_user(client: AsyncClient) -> dict:
    return await create_test_user(client, username="other", email="other@example.com")


@pytest.mark.anyio
async def test_get_me(client: AsyncClient, user: dict, auth_headers: dict):
    response = await client.get("/users/me", headers=auth_headers)

    assert response.status_code == 200
    assert response.json() == {
        "id": user["id"],
        "username": "testuser",
        "email": "test@example.com",
    }


@pytest.mark.anyio
async def test_get_me_without_token(client: AsyncClient):
    response = await client.get("/users/me")

    assert response.status_code == 401


@pytest.mark.anyio
async def test_update_own_user(client: AsyncClient, user: dict, auth_headers: dict):
    response = await client.patch(
        f"/users/{user['id']}",
        json={"username": "pepe2"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json() == {"id": user["id"], "username": "pepe2", "email": "test@example.com"}


@pytest.mark.anyio
async def test_update_without_token(client: AsyncClient, user: dict):
    response = await client.patch(f"/users/{user['id']}", json={"username": "hacked"})

    assert response.status_code == 401
    profile = await client.get(f"/users/{user['id']}")
    assert profile.json()["username"] == "testuser"


@pytest.mark.anyio
async def test_update_another_user_is_forbidden(client: AsyncClient, auth_headers: dict):
    other = await create_other_user(client)

    response = await client.patch(
        f"/users/{other['id']}",
        json={"username": "hacked"},
        headers=auth_headers,
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "Not authorized to perform this action."}
    profile = await client.get(f"/users/{other['id']}")
    assert profile.json()["username"] == "other"


@pytest.mark.anyio
async def test_update_not_exist_user(client: AsyncClient, auth_headers: dict):
    response = await client.patch(
        "/users/999999",
        json={"username": "pepe2"},
        headers=auth_headers,
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "Not authorized to perform this action."}


@pytest.mark.anyio
async def test_update_username_exist(client: AsyncClient, user: dict, auth_headers: dict):
    await create_other_user(client)

    response = await client.patch(
        f"/users/{user['id']}",
        json={"username": "other"},
        headers=auth_headers,
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "Username already exists."}


@pytest.mark.anyio
async def test_update_email_exist(client: AsyncClient, user: dict, auth_headers: dict):
    await create_other_user(client)

    response = await client.patch(
        f"/users/{user['id']}",
        json={"email": "other@example.com"},
        headers=auth_headers,
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "Email already exists."}


@pytest.mark.anyio
async def test_delete_own_user(client: AsyncClient, user: dict, auth_headers: dict):
    response = await client.delete(f"/users/{user['id']}", headers=auth_headers)

    assert response.status_code == 204
    assert response.content == b""
    profile = await client.get(f"/users/{user['id']}")
    assert profile.status_code == 404


@pytest.mark.anyio
async def test_token_is_rejected_after_deleting_own_user(
    client: AsyncClient, user: dict, auth_headers: dict
):
    await client.delete(f"/users/{user['id']}", headers=auth_headers)

    response = await client.get("/users/me", headers=auth_headers)

    assert response.status_code == 401


@pytest.mark.anyio
async def test_delete_without_token(client: AsyncClient, user: dict):
    response = await client.delete(f"/users/{user['id']}")

    assert response.status_code == 401
    profile = await client.get(f"/users/{user['id']}")
    assert profile.status_code == 200


@pytest.mark.anyio
async def test_delete_another_user_is_forbidden(client: AsyncClient, auth_headers: dict):
    other = await create_other_user(client)

    response = await client.delete(f"/users/{other['id']}", headers=auth_headers)

    assert response.status_code == 403
    profile = await client.get(f"/users/{other['id']}")
    assert profile.status_code == 200


@pytest.mark.anyio
async def test_other_user_can_still_log_in_after_forbidden_delete(
    client: AsyncClient, auth_headers: dict
):
    other = await create_other_user(client)
    await client.delete(f"/users/{other['id']}", headers=auth_headers)

    other_headers = await login(client, username="other")
    response = await client.get("/users/me", headers=other_headers)

    assert response.status_code == 200
