from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
from typing import Any

from .models import CategoriesTable


async def get_all_categories_as_list_of_dict(session: AsyncSession) -> list[dict[str, Any]]:
    "Возвращает список словарей, которые являются отражением записи в бд по принципу ключ=столбей значение=значение столбца. Если записей нет то возвразает пустой список"
    try:
        stmt = select(CategoriesTable.id, CategoriesTable.name)
        result = await session.execute(stmt)
        return [dict(res) for res in result.mappings()]
    except Exception as exc:
        logger.error(exc)
        return []

