from sqlalchemy import select
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
    Возвращает список словарей с полями карточки необходимыми для отображения в списке + имя и описание компании в каждой карточке

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
    Возвращает словарь с информацией о конкретной карточке по ее id. Если карточки нет возвращает пустой словарь

    :param card_id: Идентификатор карточки cards.id
    :param session: Асинхронная сессия SQLAlchemy
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


async def get_all_rows_from_table(table: BaseTable, session: AsyncSession) -> list[dict]:
    """
    Возвращает все строки из таблицы

    :param table: Модель представляющая собой таблицу в базе данных
    :param session: Асинхронная сессия SQLAlchemy
    """
    try:
        stmt = select(*table.__table__.columns)
        result = await session.execute(stmt)
        return [dict(res) for res in result.mappings().all()]
    except Exception as exc:
        logger.error(exc)
        return []


async def get_full_card_info_for_admin_by_card_id(card_id: int, session: AsyncSession):
    """
    Возвращает словарь с информацией о конкретной карточке по ее id с полной информацией о ней для редактирования на страницу админа\n
    Если карточки нет возвращает пустой словарь

    :param card_id: Идентификатор карточки cards.id
    :param session: Асинхронная сессия SQLAlchemy
    """
    try:
        stmt = select(
                CardsTable.category_id,
                CardsTable.company_id,
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

