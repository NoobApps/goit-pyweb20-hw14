import pickle
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from auth.auth import create_tokens
from auth.dependencies import get_current_user
from models import User


class TestAsyncAuthDependencies(unittest.IsolatedAsyncioTestCase):

    def setUp(self) -> None:
        self.user = User(
            id=1,
            email="test_user@example.com",
            hashed_password="qwerty",
            confirmed=True,
            avatar=None,
        )
        self.token = create_tokens({"sub": self.user.email})["access_token"]
        self.session = AsyncMock(spec=AsyncSession)

    @patch("auth.dependencies.redis_client")
    async def test_get_current_user_from_redis(self, mocked_redis):
        mocked_redis.get = AsyncMock(return_value=pickle.dumps(self.user))

        result = await get_current_user(token=self.token, db=self.session)
        self.assertIsInstance(result, User)
        self.assertEqual(result.id, self.user.id)
        self.assertEqual(result.email, self.user.email)
        self.session.execute.assert_not_called()

    @patch("auth.dependencies.redis_client")
    async def test_get_current_user_from_db(self, mocked_redis):
        mocked_redis.get = AsyncMock(return_value=None)
        mocked_redis.set = AsyncMock()

        mocked_user = MagicMock()
        mocked_user.scalar_one_or_none.return_value = self.user
        self.session.execute.return_value = mocked_user

        result = await get_current_user(token=self.token, db=self.session)
        self.assertEqual(result, self.user)
        mocked_redis.set.assert_called_once()

    @patch("auth.dependencies.redis_client")
    async def test_get_current_user_unconfirmed(self, mocked_redis):
        unconfirmed_user = User(
            id=2,
            email=self.user.email,
            hashed_password="qwerty",
            confirmed=False,
        )
        mocked_redis.get = AsyncMock(return_value=pickle.dumps(unconfirmed_user))

        with self.assertRaises(HTTPException) as context:
            await get_current_user(token=self.token, db=self.session)
        self.assertEqual(context.exception.status_code, 401)

    async def test_get_current_user_invalid_token(self):
        with self.assertRaises(HTTPException) as context:
            await get_current_user(token="invalid_token", db=self.session)
        self.assertEqual(context.exception.status_code, 401)


if __name__ == "__main__":
    unittest.main()