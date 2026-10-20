import pytest
from httpx import AsyncClient

from tests.conftest import create_test_user


@pytest.mark.anyio
async def test_create_user_ok(client: AsyncClient):
    response = await client.post(
        "/users",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpassword123"
        },
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
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpassword123"
        },
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "Email already exists."}

@pytest.mark.anyio
async def test_create_user_username_already_exist(client: AsyncClient):
    await create_test_user(client)

    response = await client.post(
        "/users",
        json={
            "username": "testuser",
            "email": "test2@example.com",
            "password": "testpassword123"
        },
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "Username already exists."}

@pytest.mark.anyio
async def test_get_user_that_already_exist(client: AsyncClient):
    user = await create_test_user(client)

    response = await client.get(
        "/users"
    )

    assert response.status_code == 200
    assert response.json() == [
        {"id": user["id"], "username": "testuser", "email": "test@example.com"}
    ]

@pytest.mark.anyio
async def test_get_user_without_users(client: AsyncClient):

    response = await client.get(
        "/users"
    )

    assert response.status_code == 200
    assert response.json() == []



@pytest.mark.anyio
async def test_get_user_by_id_not_exist(client: AsyncClient):
    user_id = 1
    response = await client.get(
        f"/users/{user_id}"
    )

    assert response.status_code == 404
    assert response.json() == {'detail': 'User not found.',}



@pytest.mark.anyio
async def test_get_user_by_id_exist(client: AsyncClient):
    user = await create_test_user(client)
    response = await client.get(
        f"/users/{user["id"]}"
    )

    assert response.status_code == 200
    assert response.json() == {
        "id": user["id"], "username": "testuser", "email": "test@example.com"
    }


@pytest.mark.anyio
async def test_update_correct(client: AsyncClient):
    user = await create_test_user(client)

    response = await client.patch(
        f"/users/{user["id"]}",
        json={"username": "pepe2"}
    )

    assert response.status_code == 200
    assert response.json() == {"id": user["id"], "username": "pepe2", 'email': 'test@example.com'}
    


@pytest.mark.anyio
async def test_update_not_exist_user(client: AsyncClient):

    response = await client.patch(
        "/users/1",
        json={"username": "pepe2"}
    )

    assert response.status_code == 404
    assert response.json() == {'detail': 'User not found.',}


@pytest.mark.anyio
async def test_update_username_exist(client: AsyncClient):
    user = await create_test_user(client)
    await create_test_user(client, username="pepe", email= "pepe@example.com")

    response = await client.patch(
        f"/users/{user["id"]}",
        json={"username": "pepe"}
    )

    assert response.status_code == 409
    assert response.json() == {'detail': 'Username already exists.',}
    

@pytest.mark.anyio
async def test_update_email_exist(client: AsyncClient):
    user = await create_test_user(client)
    await create_test_user(client, username="pepe", email= "pepe@example.com")

    response = await client.patch(
        f"/users/{user["id"]}",
        json={"email": "pepe@example.com"}
    )

    assert response.status_code == 409
    assert response.json() == {'detail': 'Email already exists.',}



@pytest.mark.anyio
async def test_delete_user(client: AsyncClient):
    user = await create_test_user(client)

    response = await client.delete(f"/users/{user["id"]}")

    assert response.status_code == 204
    assert response.content == b""

    response = await client.get(
            f"/users/{user["id"]}"
        )
    
    assert response.status_code == 404

