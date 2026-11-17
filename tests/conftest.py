import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from main import app
from database import get_db
from auth.dependencies import get_current_user
from models import User


@pytest.fixture
def test_user() -> User:
    """Повертає тестового підтвердженого користувача."""
    return User(
        id=1,
        email="test@example.com",
        hashed_password="hashed_password",
        confirmed=True,
        avatar=None,
    )


@pytest.fixture
def mock_db_session() -> AsyncMock:
    """Повертає мок асинхронної сесії бази даних."""
    session = AsyncMock(spec=AsyncSession)
    session.add = MagicMock()
    return session


@pytest_asyncio.fixture
async def client(mock_db_session: AsyncMock, test_user: User):
    """Створює асинхронний тестовий клієнт із перевизначеними залежностями."""

    async def override_get_db():
        yield mock_db_session

    async def override_get_current_user():
        return test_user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()