from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, extract, and_
from datetime import date, timedelta
from models import Contact
from contacts.schemas import ContactCreate, ContactUpdate
from logger import logger


async def create_contact(db: AsyncSession, contact_data: ContactCreate, user_id: int) -> Contact:
    """Створює новий контакт для вказаного користувача.

    Args:
        db (AsyncSession): Асинхронна сесія бази даних.
        contact (ContactCreate): Валідовані дані нового контакту.
        user_id (int): Ідентифікатор власника контакту.

    Returns:
        Contact: Створений об'єкт контакту.
    """
    contact = Contact(**contact_data.model_dump(), user_id=user_id)
    db.add(contact)
    await db.commit()
    await db.refresh(contact)
    logger.info(f"Створено контакт ID={contact.id} для користувача ID={user_id}")
    return contact


async def get_contacts(
    db: AsyncSession, 
    user_id: int,
    skip: int = 0, 
    limit: int = 100, 
    query: str | None = None
) -> list[Contact]:
    """Отримує список контактів користувача з підтримкою пагінації та пошуку.

    Args:
        db (AsyncSession): Асинхронна сесія бази даних.
        user_id (int): Ідентифікатор власника контактів.
        skip (int, optional): Кількість записів для пропуску. За замовчуванням 0.
        limit (int, optional): Максимальна кількість записів. За замовчуванням 100.
        search (str | None, optional): Пошуковий запит за ім'ям, прізвищем або email.

    Returns:
        list[Contact]: Список знайдених контактів.
    """
    stmt = select(Contact).where(Contact.user_id == user_id)
    if query:
        search_pattern = f"%{query}%"
        stmt = stmt.where(
            or_(
                Contact.first_name.ilike(search_pattern),
                Contact.last_name.ilike(search_pattern),
                Contact.email.ilike(search_pattern)
            )
        )
    stmt = stmt.offset(skip).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_contact_by_id(db: AsyncSession, contact_id: int, user_id: int) -> Contact | None:
    """Отримує конкретний контакт за його ID, якщо він належить користувачеві.

    Args:
        db (AsyncSession): Асинхронна сесія бази даних.
        contact_id (int): Унікальний ідентифікатор контакту.
        user_id (int): Ідентифікатор власника контакту.

    Returns:
        Contact | None: Об'єкт контакту або None, якщо запис не знайдено.
    """
    stmt = select(Contact).where(and_(Contact.id == contact_id, Contact.user_id == user_id))
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def update_contact(db: AsyncSession, contact_id: int, contact_data: ContactUpdate, user_id: int) -> Contact | None:
    """Оновлює дані існуючого контакту користувача.

    Args:
        db (AsyncSession): Асинхронна сесія бази даних.
        contact_id (int): Ідентифікатор контакту для оновлення.
        contact_data (ContactUpdate): Поля, які потрібно оновити.
        user_id (int): Ідентифікатор власника контакту.

    Returns:
        Contact | None: Оновлений об'єкт контакту або None, якщо контакт не знайдено.
    """
    contact = await get_contact_by_id(db, contact_id, user_id)
    if not contact:
        return None
    
    update_dict = contact_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(contact, key, value)

    await db.commit()
    await db.refresh(contact)
    logger.info(f"Оновлено контакт ID={contact_id} користувача ID={user_id}")
    return contact


async def delete_contact(db: AsyncSession, contact_id: int, user_id: int) -> Contact | None:
    """Видаляє контакт із бази даних за його ID.

    Args:
        db (AsyncSession): Асинхронна сесія бази даних.
        contact_id (int): Ідентифікатор контакту.
        user_id (int): Ідентифікатор власника контакту.

    Returns:
        bool: True, якщо контакт успішно видалено, інакше False.
    """
    contact = await get_contact_by_id(db, contact_id, user_id)
    if not contact:
        return None
    
    await db.delete(contact)
    await db.commit()
    logger.info(f"Видалено контакт ID={contact_id} користувача ID={user_id}")
    return contact


async def get_upcoming_birthdays(db: AsyncSession, user_id: int, days: int = 7) -> list[Contact]:
    """Повертає контакти користувача, у яких день народження припадає на найближчі 7 днів.

    Args:
        db (AsyncSession): Асинхронна сесія бази даних.
        user_id (int): Ідентифікатор власника контактів.

    Returns:
        list[Contact]: Список контактів з найближчими днями народження.
    """
    today = date.today()
    upcoming_dates = [(today + timedelta(days=i)) for i in range(days + 1)]
    date_conditions = [
        and_(
            extract('month', Contact.birthday) == d.month,
            extract('day', Contact.birthday) == d.day
        )
        for d in upcoming_dates
    ]
    
    stmt = select(Contact).where(
        and_(
            Contact.user_id == user_id,
            or_(*date_conditions)
        )
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())