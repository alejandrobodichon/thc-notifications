import os

os.environ.setdefault("API_URL", "http://api.test")
os.environ.setdefault("INTERNAL_API_KEY", "test-internal-api-key")

import pytest

pytest_plugins = ["anyio"]


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"
