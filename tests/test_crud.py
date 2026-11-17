import unittest
from datetime import date
from unittest.mock import MagicMock, AsyncMock

from sqlalchemy.ext.asyncio import AsyncSession

from models import Contact, User
from contacts.schemas import ContactCreate, ContactUpdate
from contacts.crud import (
    create_contact,
    get_contacts,
    get_contact_by_id,
    update_contact,
    delete_contact,
    get_upcoming_birthdays,
)


class TestAsyncContacts(unittest.IsolatedAsyncioTestCase):

    def setUp(self) -> None:
        self.user = User(id=1, email="test_user@example.com", hashed_password="qwerty", confirmed=True)
        self.session = AsyncMock(spec=AsyncSession)

    async def test_get_contacts(self):
        skip = 0
        limit = 10
        contacts = [
            Contact(
                id=1,
                first_name="Іван",
                last_name="Петренко",
                email="ivan@example.com",
                phone="+380501111111",
                birthday=date(1990, 5, 10),
                user_id=self.user.id,
            ),
            Contact(
                id=2,
                first_name="Олена",
                last_name="Коваленко",
                email="olena@example.com",
                phone="+380502222222",
                birthday=date(1995, 8, 20),
                user_id=self.user.id,
            ),
        ]
        mocked_contacts = MagicMock()
        mocked_contacts.scalars.return_value.all.return_value = contacts
        self.session.execute.return_value = mocked_contacts

        result = await get_contacts(self.session, self.user.id, skip=skip, limit=limit)
        self.assertEqual(result, contacts)

    async def test_get_contact_by_id(self):
        contact = Contact(
            id=1,
            first_name="Іван",
            last_name="Петренко",
            email="ivan@example.com",
            phone="+380501111111",
            birthday=date(1990, 5, 10),
            user_id=self.user.id,
        )
        mocked_contact = MagicMock()
        mocked_contact.scalar_one_or_none.return_value = contact
        self.session.execute.return_value = mocked_contact

        result = await get_contact_by_id(self.session, 1, self.user.id)
        self.assertEqual(result, contact)

    async def test_create_contact(self):
        body = ContactCreate(
            first_name="Іван",
            last_name="Петренко",
            email="ivan@example.com",
            phone="+380501111111",
            birthday=date(1990, 5, 10),
            additional_data="Тестовий контакт",
        )
        result = await create_contact(self.session, body, self.user.id)
        self.assertIsInstance(result, Contact)
        self.assertEqual(result.first_name, body.first_name)
        self.assertEqual(result.last_name, body.last_name)
        self.assertEqual(result.email, body.email)
        self.assertEqual(result.phone, body.phone)

    async def test_update_contact(self):
        body = ContactUpdate(
            first_name="Оновлене Ім'я",
            last_name="Оновлене Прізвище",
            email="updated@example.com",
            phone="+380679999999",
            birthday=date(1992, 1, 15),
        )
        mocked_contact = MagicMock()
        mocked_contact.scalar_one_or_none.return_value = Contact(
            id=1,
            first_name="Іван",
            last_name="Петренко",
            email="ivan@example.com",
            phone="+380501111111",
            birthday=date(1990, 5, 10),
            user_id=self.user.id,
        )
        self.session.execute.return_value = mocked_contact

        result = await update_contact(self.session, 1, body, self.user.id)
        self.assertIsInstance(result, Contact)
        self.assertEqual(result.first_name, body.first_name)
        self.assertEqual(result.last_name, body.last_name)
        self.assertEqual(result.email, body.email)
        self.assertEqual(result.phone, body.phone)

    async def test_delete_contact(self):
        mocked_contact = MagicMock()
        mocked_contact.scalar_one_or_none.return_value = Contact(
            id=1,
            first_name="Іван",
            last_name="Петренко",
            email="ivan@example.com",
            phone="+380501111111",
            birthday=date(1990, 5, 10),
            user_id=self.user.id,
        )
        self.session.execute.return_value = mocked_contact

        result = await delete_contact(self.session, 1, self.user.id)
        self.session.delete.assert_called_once()
        self.session.commit.assert_called_once()
        self.assertIsInstance(result, Contact)

    async def test_get_upcoming_birthdays(self):
        contacts = [
            Contact(
                id=1,
                first_name="Іван",
                last_name="Петренко",
                email="ivan@example.com",
                phone="+380501111111",
                birthday=date.today(),
                user_id=self.user.id,
            )
        ]
        mocked_contacts = MagicMock()
        mocked_contacts.scalars.return_value.all.return_value = contacts
        self.session.execute.return_value = mocked_contacts

        result = await get_upcoming_birthdays(self.session, self.user.id)
        self.assertEqual(result, contacts)


if __name__ == "__main__":
    unittest.main()