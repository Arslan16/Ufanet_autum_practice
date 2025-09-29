from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
from typing import Any

from .models import CardsTable, CategoriesTable, CompaniesTable


async def get_all_categories(session: AsyncSession) -> list[dict[str, Any]]:
    "Возвращает список словарей, которые являются отражением записи в бд по принципу ключ=столбей значение=значение столбца. Если записей нет то возвразает пустой список"
    try:
        stmt = select(CategoriesTable.id, CategoriesTable.name)
        result = await session.execute(stmt)
        return [dict(res) for res in result.mappings()]
    except Exception as exc:
        logger.error(exc)
        return []


async def get_all_cards_in_category_with_short_description(category_id: int, session: AsyncSession) -> list[dict]:
    "Возвращает список словарей с полями карточки необходимыми для отображения в списке + имя и описание компании в каждой карточке"
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
