import pytest
from datetime import date
from unittest.mock import AsyncMock, patch
from models import Contact


@pytest.fixture
def sample_contact() -> Contact:
    return Contact(
        id=1,
        first_name="Іван",
        last_name="Петренко",
        email="ivan@example.com",
        phone="+380501112233",
        birthday=date(1990, 5, 15),
        additional_data="Колега",
        user_id=1,
    )


@pytest.mark.asyncio
async def test_create_contact_route(client, sample_contact):
    """Перевіряє POST /contacts/ — створення нового контакту."""
    payload = {
        "first_name": "Іван",
        "last_name": "Петренко",
        "email": "ivan@example.com",
        "phone": "+380501112233",
        "birthday": "1990-05-15",
        "additional_data": "Колега",
    }

    with patch("contacts.router.crud.create_contact", new_callable=AsyncMock) as mock_create:
        mock_create.return_value = sample_contact
        response = await client.post("/contacts/", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["id"] == 1
    assert data["first_name"] == "Іван"
    assert data["email"] == "ivan@example.com"


@pytest.mark.asyncio
async def test_get_contacts_route(client, sample_contact):
    """Перевіряє GET /contacts/ — отримання списку контактів."""
    with patch("contacts.router.crud.get_contacts", new_callable=AsyncMock) as mock_get_all:
        mock_get_all.return_value = [sample_contact]
        response = await client.get("/contacts/")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["email"] == "ivan@example.com"


@pytest.mark.asyncio
async def test_get_contact_by_id_route(client, sample_contact):
    """Перевіряє GET /contacts/{contact_id} — успішне отримання та 404 при відсутності."""
    with patch("contacts.router.crud.get_contact_by_id", new_callable=AsyncMock) as mock_get_one:
        mock_get_one.return_value = sample_contact
        response = await client.get("/contacts/1")
        assert response.status_code == 200
        assert response.json()["id"] == 1

        mock_get_one.return_value = None
        response_not_found = await client.get("/contacts/999")
        assert response_not_found.status_code == 404


@pytest.mark.asyncio
async def test_update_contact_route(client, sample_contact):
    """Перевіряє PUT /contacts/{contact_id} (або PATCH) — оновлення контакту."""
    updated_contact = Contact(
        id=1,
        first_name="Олег",
        last_name="Петренко",
        email="ivan@example.com",
        phone="+380501112233",
        birthday=date(1990, 5, 15),
        additional_data="Колега",
        user_id=1,
    )
    payload = {
        "first_name": "Олег",
        "last_name": "Петренко",
        "email": "ivan@example.com",
        "phone": "+380501112233",
        "birthday": "1990-05-15",
    }

    with patch("contacts.router.crud.update_contact", new_callable=AsyncMock) as mock_update:
        mock_update.return_value = updated_contact
        response = await client.put("/contacts/1", json=payload)

    assert response.status_code == 200
    assert response.json()["first_name"] == "Олег"


@pytest.mark.asyncio
async def test_delete_contact_route(client, sample_contact):
    """Перевіряє DELETE /contacts/{contact_id} — видалення контакту."""
    with patch("contacts.router.crud.delete_contact", new_callable=AsyncMock) as mock_delete:
        mock_delete.return_value = sample_contact
        response = await client.delete("/contacts/1")
        assert response.status_code in (200, 204)

        mock_delete.return_value = None
        response_missing = await client.delete("/contacts/999")
        assert response_missing.status_code == 404


@pytest.mark.asyncio
async def test_upcoming_birthdays_route(client, sample_contact):
    """Перевіряє GET /contacts/birthdays — отримання найближчих днів народження."""
    with patch("contacts.router.crud.get_upcoming_birthdays", new_callable=AsyncMock) as mock_bdays:
        mock_bdays.return_value = [sample_contact]
        response = await client.get("/contacts/upcoming-birthdays")

    assert response.status_code == 200
    assert len(response.json()) == 1

@pytest.mark.asyncio
async def test_update_contact_not_found_route(client):
    """Перевіряє PUT /contacts/{contact_id} — повернення 404, якщо контакт не знайдено."""
    payload = {"first_name": "Олег"}
    with patch("contacts.router.crud.update_contact", new_callable=AsyncMock) as mock_update:
        mock_update.return_value = None
        response = await client.put("/contacts/999", json=payload)

    assert response.status_code == 404