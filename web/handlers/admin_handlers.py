from fastapi import APIRouter, Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any
from loguru import logger

from config import TEMPLATES
from core.models import BaseTable, CardsTable, CompaniesTable, CategoriesTable, dict_tables
from core.database_utils import get_all_rows_from_table, get_full_card_info_for_admin_by_card_id
from ..dependencies import async_session_generator
from ..schemas import GetTableDataModel, CardPydanticModel


admin_rt = APIRouter(prefix="/admin")
"Роутер отвечающий за обработку запросов для администратора"


@admin_rt.get("/")
async def index_get_handler(request: Request):
    return TEMPLATES.TemplateResponse(request, "admin/index.html", {"tables": {"Комании": CompaniesTable.__tablename__, "Карточки": CardsTable.__tablename__, "Категории": CategoriesTable.__tablename__}})


@admin_rt.post("/get_table_data")
async def get_table_data(request: Request, data: GetTableDataModel, session: AsyncSession = Depends(async_session_generator)):
    if dict_tables.get(data.tablename) is not None:
        table: BaseTable = dict_tables.get(data.tablename)
        "Модель таблицы базы данных извлеченная по ее названию"
        
        rows: list[dict[str, Any]] = await get_all_rows_from_table(table, session)
        "Список словарей отражающих запись в базе данных по принципу ключ:столбец значение:значение столбца"
        
        logger.debug(f"{rows=}")
        return TEMPLATES.TemplateResponse(request, "admin/table.html", {"columns": [column.name for column in table.__table__.columns], "rows": rows})


@admin_rt.post("/get_card_info")
async def get_card_info_post_handler(request: Request, data: CardPydanticModel, session: AsyncSession = Depends(async_session_generator)):
    "Обрабатывает запрос на получение информации о карточке. Выдает отрендеренное модальное окно"
    card_info: dict[str, Any] = await get_full_card_info_for_admin_by_card_id(data.card_id, session)
    "Информация о конкретной карточке извлеченной по ее ид, содержащая полуню информацию о ней для редактирования админом"
    logger.debug(f"{card_info=}")
    return TEMPLATES.TemplateResponse(request, "admin/cards_modal.html", {"card": card_info})
