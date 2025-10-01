from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
from typing import Any

from .models import BaseTable, CardsTable, CategoriesTable, CompaniesTable


async def get_all_categories(session: AsyncSession) -> list[dict[str, Any]]:
    """
    Возвращает список словарей с данными категорий из БД.

    :param session: Асинхронная сессия SQLAlchemy
    :rtype: list[dict[str, Any]]
    :return: Список словарей, где ключ = имя столбца, значение = значение столбца.
    """
    try:
        stmt = select(CategoriesTable.id, CategoriesTable.name)
        result = await session.execute(stmt)
        return [dict(res) for res in result.mappings()]
    except Exception as exc:
        logger.error(exc)
        return []


async def get_all_cards_in_category_with_short_description(category_id: int, session: AsyncSession) -> list[dict[str, Any]]:
    """
    Извлекает карточки в категории с данными необходимыми для отображения в списке + имя и описание компании в каждой карточке

    :param category_id: Идентификатор категории. Таблица categories.id
    :param session: Асинхронная сессия SQLAlchemy
    :rtype: list[dict[str, Any]]
    :return: Список словарей, где ключ = имя столбца, значение = значение столбца.
    """
    try:
        stmt = select(
                CardsTable.id,
                CardsTable.main_label,
                CardsTable.description_under_label,
                CompaniesTable.name.label("company_name"),
                CompaniesTable.short_description.label("company_short_description")
            ).where(CardsTable.category_id == category_id
            ).join(CompaniesTable, CompaniesTable.id == CardsTable.company_id
        )
        result = await session.execute(stmt)
        return [dict(res) for res in result.mappings()]
    except Exception as exc:
        logger.error(exc)
        return []


async def get_card_info_by_card_id(card_id: int, session: AsyncSession) -> dict[str, Any]:
    """
    Извлекает информацию о конкретной карточке по ее id. Если карточки нет возвращает пустой словарь

    :param card_id: Идентификатор карточки cards.id
    :param session: Асинхронная сессия SQLAlchemy
    :rtype: dict[str, Any]
    :return: Словарь, где ключ = имя столбца, значение = значение столбца.
    """
    try:
        stmt = select(
                CardsTable.main_label,
                CardsTable.description_under_label,
                CardsTable.obtain_method_description,
                CardsTable.validity_period,
                CardsTable.about_partner,
                CardsTable.promocode,
                CardsTable.call_to_action_link,
                CardsTable.call_to_action_btn_label
            ).where(CardsTable.id == card_id
        )
        result = await session.execute(stmt)
        return dict(result.mappings().first())
    except Exception as exc:
        logger.error(exc)
        return {}


async def get_all_rows_from_table(table: BaseTable, session: AsyncSession) -> list[dict[str, Any]]:
    """
    Возвращает все строки из таблицы

    :param table: Модель представляющая собой таблицу в базе данных
    :param session: Асинхронная сессия SQLAlchemy
    :rtype: list[dict[str, Any]]
    :return: Список словарей, где ключ = имя столбца, значение = значение столбца.
    """
    try:
        stmt = select(*table.__table__.columns)
        result = await session.execute(stmt)
        return [dict(res) for res in result.mappings().all()]
    except Exception as exc:
        logger.error(exc)
        return []


async def get_full_row_for_admin_by_id(row_id: int, table: BaseTable, session: AsyncSession) -> dict[str, Any]:
    """
    Возвращает словарь с информацией о конкретной записи по ее id с полной информацией о ней для редактирования на страницу админа\n
    Если записи нет возвращает пустой словарь

    :param row_id: Идентификатор записи id
    :param table: Ссылка на модель, представляющую таблицу
    :param session: Асинхронная сессия SQLAlchemy
    :rtype: dict[str, Any]
    :return: Словарь, где ключ = имя столбца, значение = значение столбца.
    """
    try:
        stmt = select(
                *table.__table__.columns
            ).where(table.id == row_id
        )
        result = await session.execute(stmt)
        return dict(result.mappings().first())
    except Exception as exc:
        logger.error(exc)
        return {}


async def update_row_by_id(row_id: int, table: BaseTable, data: dict[str, Any], session: AsyncSession) -> bool:
    """
    Обновляет информацию о записи в таблице по ее id, 

    :param row_id: Идентификатор записи id
    :param table: Ссылка на модель, представляющую таблицу
    :param session: Асинхронная сессия SQLAlchemy
    :rtype: bool
    :return: True если обновление успешно иначе False
    """
    try:
        stmt = update(table).values(**data).where(table.id == row_id)
        await session.execute(stmt)
        await session.commit()
        return True
    except Exception as exc:
        logger.error(exc)
        return False


