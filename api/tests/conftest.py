import os
from collections.abc import AsyncGenerator

os.environ.setdefault(
    "DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost/test_thc"
)
os.environ.setdefault("SECRET_KEY", "test-secret-key-at-least-32-bytes-long")
os.environ.setdefault("SQS_ENDPOINT_URL", "http://localhost:9324")
os.environ.setdefault("INTERNAL_API_KEY", "test-internal-api-key")

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from clients.sms_queue_publisher import SmsQueuePublisher
from core.database import Base, get_db
from core.exceptions import SmsQueueUnavailable
from dependencies import get_sms_publisher
from main import app

pytest_plugins = ["anyio"]


class FakeSmsPublisher(SmsQueuePublisher):
    """Stands in for SmsQueuePublisher: records messages instead of sending them to SQS."""

    def __init__(self) -> None:  # no SQS client needed

        self.messages: list[dict] = []
        self.fail = False

    async def publish(self, notification_id: int, to: str, message: str) -> None:
        if self.fail:
            raise SmsQueueUnavailable()
        self.messages.append({"notification_id": notification_id, "to": to, "message": message})


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="session")
def test_engine():
    engine = create_async_engine(
        os.environ["DATABASE_URL"],
        poolclass=NullPool,
    )
    return engine


@pytest.fixture(scope="session")
async def setup_database(test_engine):
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await test_engine.dispose()


@pytest.fixture
async def db_session(
    test_engine,
    setup_database,
) -> AsyncGenerator[AsyncSession]:
    conn = await test_engine.connect()
    trans = await conn.begin()

    test_async_session = async_sessionmaker(
        bind=conn,
        class_=AsyncSession,
        expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )

    async with test_async_session() as session:
        try:
            yield session
        finally:
            await session.close()
            await trans.rollback()
            await conn.close()


@pytest.fixture
def sms_publisher() -> FakeSmsPublisher:
    return FakeSmsPublisher()


@pytest.fixture
async def client(
    db_session: AsyncSession,
    sms_publisher: FakeSmsPublisher,
) -> AsyncGenerator[AsyncClient]:

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_sms_publisher] = lambda: sms_publisher

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


async def create_test_user(
    client: AsyncClient,
    username: str = "testuser",
    email: str = "test@example.com",
    password: str = "testpassword123",
) -> dict:
    response = await client.post(
        "/users",
        json={
            "username": username,
            "email": email,
            "password": password,
        },
    )
    assert response.status_code == 201, f"Failed to create user: {response.text}"
    return response.json()


async def login(
    client: AsyncClient,
    username: str = "testuser",
    password: str = "testpassword123",
) -> dict[str, str]:
    response = await client.post(
        "/auth/token",
        data={"username": username, "password": password},
    )
    assert response.status_code == 200, f"Failed to log in: {response.text}"
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.fixture
async def user(client: AsyncClient) -> dict:
    return await create_test_user(client)


@pytest.fixture
async def auth_headers(client: AsyncClient, user: dict) -> dict[str, str]:
    return await login(client)
