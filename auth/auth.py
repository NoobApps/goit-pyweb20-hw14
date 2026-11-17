from datetime import datetime, timedelta, timezone
import jwt
from passlib.context import CryptContext
from config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Перевіряє відповідність відкритого пароля його хешу.

    Args:
        plain_password (str): Пароль у відкритому вигляді.
        hashed_password (str): Хешований пароль із бази даних.

    Returns:
        bool: True, якщо пароль збігається, інакше False.
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Генерує безпечний bcrypt-хеш для заданого пароля.

    Args:
        password (str): Пароль у відкритому вигляді.

    Returns:
        str: Хешований рядок пароля.
    """
    return pwd_context.hash(password)


def create_tokens(data: dict) -> dict:
    """Створює пару JWT-токенів (access та refresh) для користувача.

    Args:
        data (dict): Дані (payload), які потрібно закодувати в токен (наприклад, {'sub': email}).

    Returns:
        dict[str, str]: Словник із ключами 'access_token', 'refresh_token' та 'token_type'.
    """
    access_payload = data.copy()
    access_expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_payload.update({"exp": access_expire, "scope": "access"})
    access_token = jwt.encode(access_payload,
                              settings.SECRET_KEY.get_secret_value(),
                              algorithm=settings.ALGORITHM)

    refresh_payload = data.copy()
    refresh_expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_payload.update({"exp": refresh_expire, "scope": "refresh"})
    refresh_token = jwt.encode(refresh_payload, settings.SECRET_KEY.get_secret_value(), algorithm=settings.ALGORITHM)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token
    }
def create_reset_token(email: str) -> str:
    """Генерує короткоживучий JWT-токен для процедури скидання пароля.

    Args:
        email (str): Електронна адреса користувача.

    Returns:
        str: Закодований JWT-токен зі scope 'reset_password'.
    """
    expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    payload = {"sub": email, "exp": expire, "scope": "reset_password"}
    return jwt.encode(payload, settings.SECRET_KEY.get_secret_value(), algorithm=settings.ALGORITHM)

def decode_token(token: str, expected_scope: str = "access") -> dict | None:
    """Декодує та валідує JWT-токен, перевіряючи його підпис, термін дії та область (scope).

    Args:
        token (str): Рядок JWT-токена.
        expected_scope (str, optional): Очікувана область дії токена ('access', 'refresh' або 'reset_password').

    Returns:
        dict | None: Словник із даними payload, якщо токен валідний, інакше None.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY.get_secret_value(), algorithms=[settings.ALGORITHM])
        if payload.get("scope") != expected_scope:
            return None
        return payload
    except jwt.PyJWTError:
        return None