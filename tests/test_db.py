import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db


class TestDatabase(unittest.IsolatedAsyncioTestCase):

    def setUp(self) -> None:
        self.mock_session = AsyncMock(spec=AsyncSession)
        self.mock_session_context = MagicMock()
        self.mock_session_context.__aenter__ = AsyncMock(return_value=self.mock_session)
        self.mock_session_context.__aexit__ = AsyncMock(return_value=None)

    @patch("database.AsyncSessionLocal")
    async def test_get_db_success(self, mocked_session_local):
        mocked_session_local.return_value = self.mock_session_context

        gen = get_db()
        session = await gen.__anext__()

        self.assertEqual(session, self.mock_session)

        # Завершуємо генератор (імітація успішного виконання запиту)
        with self.assertRaises(StopAsyncIteration):
            await gen.__anext__()

        self.mock_session.rollback.assert_not_called()
        self.mock_session.close.assert_awaited_once()

    @patch("database.AsyncSessionLocal")
    async def test_get_db_exception_rollback(self, mocked_session_local):
        mocked_session_local.return_value = self.mock_session_context

        gen = get_db()
        session = await gen.__anext__()
        self.assertEqual(session, self.mock_session)

        # Імітуємо виняток усередині блоку залежності
        with self.assertRaises(RuntimeError):
            await gen.athrow(RuntimeError("DB error"))

        self.mock_session.rollback.assert_awaited_once()
        self.mock_session.close.assert_awaited_once()


if __name__ == "__main__":
    unittest.main()