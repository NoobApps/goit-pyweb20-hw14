import unittest
from datetime import datetime, timedelta, timezone
import jwt

from auth.auth import (
    verify_password,
    get_password_hash,
    create_tokens,
    decode_token,
)
from auth.email import create_reset_token
from config import settings


class TestAuthModule(unittest.TestCase):

    def setUp(self) -> None:
        self.email = "test_user@example.com"
        self.password = "qwerty123"

    def test_password_hashing_and_verification(self):
        hashed = get_password_hash(self.password)
        self.assertNotEqual(self.password, hashed)
        self.assertTrue(verify_password(self.password, hashed))
        self.assertFalse(verify_password("wrong_password", hashed))

    def test_create_and_decode_tokens(self):
        tokens = create_tokens({"sub": self.email})
        self.assertIn("access_token", tokens)
        self.assertIn("refresh_token", tokens)

        access_payload = decode_token(tokens["access_token"], expected_scope="access")
        self.assertIsNotNone(access_payload)
        self.assertEqual(access_payload["sub"], self.email)
        self.assertEqual(access_payload["scope"], "access")

        refresh_payload = decode_token(tokens["refresh_token"], expected_scope="refresh")
        self.assertIsNotNone(refresh_payload)
        self.assertEqual(refresh_payload["sub"], self.email)
        self.assertEqual(refresh_payload["scope"], "refresh")

    def test_create_and_decode_reset_token(self):
        reset_token = create_reset_token(self.email)
        payload = decode_token(reset_token, expected_scope="reset_password")
        self.assertIsNotNone(payload)
        self.assertEqual(payload["sub"], self.email)
        self.assertEqual(payload["scope"], "reset_password")
        self.assertIsNone(decode_token(reset_token, expected_scope="access"))

    def test_decode_token_wrong_scope(self):
        tokens = create_tokens({"sub": self.email})
        result = decode_token(tokens["access_token"], expected_scope="refresh")
        self.assertIsNone(result)

    def test_decode_expired_token(self):
        expired_time = datetime.now(timezone.utc) - timedelta(minutes=5)
        payload = {"sub": self.email, "exp": expired_time, "scope": "access"}
        expired_token = jwt.encode(payload, settings.SECRET_KEY.get_secret_value(), algorithm=settings.ALGORITHM)
        self.assertIsNone(decode_token(expired_token, expected_scope="access"))

    def test_decode_invalid_signature_token(self):
        payload = {"sub": self.email, "scope": "access"}
        invalid_token = jwt.encode(
            payload, "WRONG_SECRET_KEY_WITH_MINIMUM_32_BYTES", algorithm=settings.ALGORITHM
        )
        self.assertIsNone(decode_token(invalid_token, expected_scope="access"))


if __name__ == "__main__":
    unittest.main()