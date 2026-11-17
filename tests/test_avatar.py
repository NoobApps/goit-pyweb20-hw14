import io
import unittest
from unittest.mock import patch

from auth.avatar import upload_avatar


class TestAvatarModule(unittest.TestCase):

    def setUp(self) -> None:
        self.mock_file = io.BytesIO(b"fake_image_binary_data")
        self.public_id = "user_42"
        self.expected_url = "https://res.cloudinary.com/demo/image/upload/v123456/avatars/user_42.jpg"

    @patch("auth.avatar.cloudinary.uploader.upload")
    def test_upload_avatar_success(self, mocked_upload):
        mocked_upload.return_value = {"secure_url": self.expected_url}

        result = upload_avatar(self.mock_file, self.public_id)

        self.assertEqual(result, self.expected_url)
        mocked_upload.assert_called_once_with(
            self.mock_file,
            public_id=f"avatars/{self.public_id}",
            overwrite=True,
            transformation=[{"width": 250, "height": 250, "crop": "fill"}],
        )

    @patch("auth.avatar.cloudinary.uploader.upload")
    def test_upload_avatar_returns_none_if_no_secure_url(self, mocked_upload):
        mocked_upload.return_value = {}

        result = upload_avatar(self.mock_file, self.public_id)

        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()