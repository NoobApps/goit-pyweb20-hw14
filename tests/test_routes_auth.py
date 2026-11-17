import io
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from auth.auth import get_password_hash, create_tokens
from auth.email import create_reset_token
from models import User


@pytest.mark.asyncio
async def test_register_user_success(client, mock_db_session):
    """Перевіряє успішну реєстрацію нового користувача (201 Created)."""
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db_session.execute.return_value = mock_result

    async def mock_refresh(instance):
        instance.id = 1

    mock_db_session.refresh.side_effect = mock_refresh

    with patch("auth.router.send_verification_email", new_callable=AsyncMock) as mock_send_email:
        response = await client.post(
            "/auth/register",
            json={"email": "newuser@example.com", "password": "strongpassword123"},
        )

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert data["id"] == 1
    mock_send_email.assert_called_once()


@pytest.mark.asyncio
async def test_register_user_conflict(client, mock_db_session, test_user):
    """Перевіряє помилку 409 Conflict при повторній реєстрації існуючого email."""
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = test_user
    mock_db_session.execute.return_value = mock_result

    response = await client.post(
        "/auth/register",
        json={"email": test_user.email, "password": "strongpassword123"},
    )

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_confirmed_email_branches(client, mock_db_session):
    """Перевіряє підтвердження пошти: невалідний токен (400), вже підтверджена (200) та нове підтвердження (200)."""
    # 1. Недійсний токен
    resp_invalid = await client.get("/auth/confirmed_email/invalid_token")
    assert resp_invalid.status_code == 400

    email = "user@example.com"
    token = create_tokens({"sub": email})["access_token"]

    # 2. Користувача не знайдено
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db_session.execute.return_value = mock_result
    resp_missing = await client.get(f"/auth/confirmed_email/{token}")
    assert resp_missing.status_code == 400

    # 3. Пошта вже підтверджена
    confirmed_user = User(id=1, email=email, hashed_password="pwd", confirmed=True)
    mock_result.scalar_one_or_none.return_value = confirmed_user
    resp_already = await client.get(f"/auth/confirmed_email/{token}")
    assert resp_already.status_code == 200
    assert "вже підтверджена" in resp_already.json()["message"]

    # 4. Успішне підтвердження
    unconfirmed_user = User(id=2, email=email, hashed_password="pwd", confirmed=False)
    mock_result.scalar_one_or_none.return_value = unconfirmed_user
    resp_ok = await client.get(f"/auth/confirmed_email/{token}")
    assert resp_ok.status_code == 200
    assert unconfirmed_user.confirmed is True
    mock_db_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_login_success_and_errors(client, mock_db_session):
    """Перевіряє вхід: успішний (200), невірний пароль (401) та непідтверджений email (401)."""
    raw_password = "MySecretPassword1"
    user = User(
        id=1,
        email="login@example.com",
        hashed_password=get_password_hash(raw_password),
        confirmed=True,
    )
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = user
    mock_db_session.execute.return_value = mock_result

    # Успішний вхід
    resp_ok = await client.post(
        "/auth/login",
        data={"username": "login@example.com", "password": raw_password},
    )
    assert resp_ok.status_code == 200
    assert "access_token" in resp_ok.json()
    assert "refresh_token" in resp_ok.json()

    # Невірний пароль
    resp_wrong_pwd = await client.post(
        "/auth/login",
        data={"username": "login@example.com", "password": "WrongPassword"},
    )
    assert resp_wrong_pwd.status_code == 401

    # Непідтверджена пошта
    user.confirmed = False
    resp_unconfirmed = await client.post(
        "/auth/login",
        data={"username": "login@example.com", "password": raw_password},
    )
    assert resp_unconfirmed.status_code == 401


@pytest.mark.asyncio
async def test_refresh_tokens_route(client, mock_db_session, test_user):
    """Перевіряє POST /auth/refresh — успішне оновлення та помилки 401."""
    tokens = create_tokens({"sub": test_user.email})

    # 1. Невалідний refresh_token
    resp_invalid = await client.post("/auth/refresh", json={"refresh_token": "bad_token"})
    assert resp_invalid.status_code == 401

    # 2. Користувача не знайдено в БД
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db_session.execute.return_value = mock_result
    resp_no_user = await client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert resp_no_user.status_code == 401

    # 3. Успішне оновлення пари токенів (201 Created)
    mock_result.scalar_one_or_none.return_value = test_user
    resp_ok = await client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert resp_ok.status_code == 201
    assert "access_token" in resp_ok.json()
    assert "refresh_token" in resp_ok.json()


@pytest.mark.asyncio
async def test_update_user_avatar_route(client, mock_db_session, test_user):
    """Перевіряє PATCH /auth/avatar — завантаження у Cloudinary та очищення кешу Redis."""
    fake_url = "https://res.cloudinary.com/demo/image/upload/avatars/1.jpg"

    with patch("auth.router.upload_avatar", return_value=fake_url) as mock_upload, \
         patch("auth.router.redis_client.delete", new_callable=AsyncMock) as mock_redis_del:
        response = await client.patch(
            "/auth/avatar",
            files={"file": ("avatar.jpg", io.BytesIO(b"fake_image_bytes"), "image/jpeg")},
        )

    assert response.status_code == 200
    assert response.json()["avatar"] == fake_url
    mock_upload.assert_called_once()
    mock_db_session.commit.assert_awaited_once()
    mock_redis_del.assert_awaited_once_with(f"user:{test_user.email}")


@pytest.mark.asyncio
async def test_request_reset_password_route(client, mock_db_session, test_user):
    """Перевіряє POST /auth/request-reset-password для існуючого та неіснуючого email."""
    mock_result = MagicMock()
    mock_db_session.execute.return_value = mock_result

    # 1. Користувач існує -> лист ставиться у фонову чергу
    mock_result.scalar_one_or_none.return_value = test_user
    with patch("auth.router.send_reset_password_email", new_callable=AsyncMock) as mock_send:
        resp_found = await client.post("/auth/request-reset-password", json={"email": test_user.email})
    assert resp_found.status_code == 200
    mock_send.assert_called_once()

    # 2. Користувач не існує -> повертає 200 без розкриття інформації та без відправки листа
    mock_result.scalar_one_or_none.return_value = None
    with patch("auth.router.send_reset_password_email", new_callable=AsyncMock) as mock_send:
        resp_not_found = await client.post("/auth/request-reset-password", json={"email": "unknown@example.com"})
    assert resp_not_found.status_code == 200
    mock_send.assert_not_called()


@pytest.mark.asyncio
async def test_reset_password_page_route(client, test_user):
    """Перевіряє GET /auth/reset-password-page/{token} — HTML-форма та помилка 400."""
    # Недійсний токен -> 400
    resp_invalid = await client.get("/auth/reset-password-page/invalid_token")
    assert resp_invalid.status_code == 400

    # Валідний reset-токен -> 200 HTML
    reset_token = create_reset_token(test_user.email)
    resp_ok = await client.get(f"/auth/reset-password-page/{reset_token}")
    assert resp_ok.status_code == 200
    assert "Новий пароль" in resp_ok.text


@pytest.mark.asyncio
async def test_reset_password_submit_route(client, mock_db_session, test_user):
    """Перевіряє POST /auth/reset-password — зміна пароля, інвалідація Redis та помилки 400/404."""
    # 1. Недійсний токен -> 400
    resp_invalid = await client.post(
        "/auth/reset-password",
        json={"token": "invalid_token", "new_password": "newpassword123"},
    )
    assert resp_invalid.status_code == 400

    reset_token = create_reset_token(test_user.email)
    mock_result = MagicMock()
    mock_db_session.execute.return_value = mock_result

    # 2. Користувача не знайдено -> 404
    mock_result.scalar_one_or_none.return_value = None
    resp_not_found = await client.post(
        "/auth/reset-password",
        json={"token": reset_token, "new_password": "newpassword123"},
    )
    assert resp_not_found.status_code == 404

    # 3. Успішна зміна пароля -> 200 + очищення кешу Redis
    mock_result.scalar_one_or_none.return_value = test_user
    with patch("auth.router.redis_client.delete", new_callable=AsyncMock) as mock_redis_del:
        resp_ok = await client.post(
            "/auth/reset-password",
            json={"token": reset_token, "new_password": "newpassword123"},
        )

    assert resp_ok.status_code == 200
    mock_db_session.commit.assert_awaited()
    mock_redis_del.assert_awaited_once_with(f"user:{test_user.email}")