import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from auth.email import send_verification_email, send_reset_password_email


class TestEmailModule(unittest.IsolatedAsyncioTestCase):

    def setUp(self) -> None:
        self.email = "test_user@example.com"
        self.host = "http://localhost:8000/"
        self.mock_token = "mocked_token_value"

    @patch("auth.email.FastMail")
    @patch("auth.email.create_tokens")
    async def test_send_verification_email(self, mocked_create_tokens, mocked_fastmail):
        mocked_create_tokens.return_value = {"access_token": self.mock_token}
        mock_fm_instance = MagicMock()
        mock_fm_instance.send_message = AsyncMock()
        mocked_fastmail.return_value = mock_fm_instance

        await send_verification_email(self.email, self.host)

        mocked_create_tokens.assert_called_once_with({"sub": self.email})
        mock_fm_instance.send_message.assert_awaited_once()

        sent_message = mock_fm_instance.send_message.call_args[0][0]
        self.assertEqual(sent_message.subject, "Підтвердження реєстрації")
        self.assertEqual(sent_message.recipients[0].email, self.email)
        self.assertIn(f"{self.host}auth/confirmed_email/{self.mock_token}", sent_message.body)

    @patch("auth.email.FastMail")
    @patch("auth.email.create_reset_token")
    async def test_send_reset_password_email(self, mocked_create_reset_token, mocked_fastmail):
        mocked_create_reset_token.return_value = self.mock_token
        mock_fm_instance = MagicMock()
        mock_fm_instance.send_message = AsyncMock()
        mocked_fastmail.return_value = mock_fm_instance

        await send_reset_password_email(self.email, self.host)

        mocked_create_reset_token.assert_called_once_with(self.email)
        mock_fm_instance.send_message.assert_awaited_once()

        sent_message = mock_fm_instance.send_message.call_args[0][0]
        self.assertEqual(sent_message.subject, "Запит на скидання паролю")
        self.assertEqual(sent_message.recipients[0].email, self.email)
        self.assertIn(self.mock_token, sent_message.body)


if __name__ == "__main__":
    unittest.main()