from fastapi import APIRouter, Request, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any
from loguru import logger

from config import TEMPLATES
from core.models import BaseTable, CardsTable, CompaniesTable, CategoriesTable, tables, russian_field_names
from core.database_utils import get_all_rows_from_table, get_full_row_for_admin_by_id, update_row_by_id, create_row
from web.utils import map_columns_to_table_types
from ..dependencies import async_session_generator
from ..schemas import GetTableDataModel, GetTableRowModel, SaveRowModel, CreateRowGetModalModel, CreateRowModel


admin_rt = APIRouter(prefix="/admin")
"Роутер отвечающий за обработку запросов для администратора"


@admin_rt.get("/")
async def index_get_handler(request: Request):
    return TEMPLATES.TemplateResponse(request, "admin/index.html", {"tables": {"Комании": CompaniesTable.__tablename__, "Карточки": CardsTable.__tablename__, "Категории": CategoriesTable.__tablename__}})


@admin_rt.post("/get_table_data")
async def get_table_data(request: Request, data: GetTableDataModel, session: AsyncSession = Depends(async_session_generator)):
    if tables.get(data.tablename) is not None:
        table: BaseTable = tables.get(data.tablename)
        "Модель таблицы базы данных извлеченная по ее названию"
        
        rows: list[dict[str, Any]] = await get_all_rows_from_table(table, session)
        "Список словарей отражающих запись в базе данных по принципу ключ:столбец значение:значение столбца"
        
        logger.debug(f"{rows=}")
        return TEMPLATES.TemplateResponse(request, "admin/table.html", {"tablename": data.tablename, "columns": [column.name for column in table.__table__.columns], "descriptions": russian_field_names, "rows": rows})


@admin_rt.post("/get_table_row")
async def get_table_row_post_handler(request: Request, data: GetTableRowModel, session: AsyncSession = Depends(async_session_generator)):
    "Обрабатывает запрос на получение информации о карточке. Выдает отрендеренное модальное окно"
    if tables.get(data.tablename) is not None:
        row_info: dict[str, Any] = await get_full_row_for_admin_by_id(data.id, tables[data.tablename], session)
        "Информация о конкретной карточке извлеченной по ее ид, содержащая полуню информацию о ней для редактирования админом"
        logger.debug(f"{row_info=}")
        return TEMPLATES.TemplateResponse(request, "admin/cards_modal_save.html", {"row_id": data.id, "row_info": row_info, "descriptions": russian_field_names, "columns": row_info.keys()})


@admin_rt.post("/save_row")
async def save_row_post_handler(data: SaveRowModel, session: AsyncSession = Depends(async_session_generator)):
    if tables.get(data.tablename) is not None:
        normalized_data: dict[str, Any] = map_columns_to_table_types(tables.get(data.tablename), data.data)
        update_res: bool = await update_row_by_id(data.id, tables.get(data.tablename), normalized_data, session)
        if update_res is True:
            return JSONResponse({"ok": True}, 200)
        else:
            return JSONResponse({"ok": False}, 500)


@admin_rt.post("/get_modal_to_create_row")
async def create_row_get_handler(request: Request, data: CreateRowGetModalModel):
    if tables.get(data.tablename) is not None:
        table: BaseTable = tables.get(data.tablename)
        columns = [column.name for column in table.__table__.columns]
        logger.debug(f"{columns=}")
        return TEMPLATES.TemplateResponse(request, "admin/cards_modal_create.html", {"descriptions": russian_field_names, "columns": columns})


@admin_rt.post("/create_row")
async def create_row_post_handler(data: CreateRowModel, session: AsyncSession = Depends(async_session_generator)):
    if tables.get(data.tablename) is not None:
        normalized_data: dict[str, Any] = map_columns_to_table_types(tables.get(data.tablename), data.data)
        res = await create_row(tables.get(data.tablename), normalized_data, session)
        if res is True:
            return JSONResponse({"ok": True}, 200)
        else:
            return JSONResponse({"ok": False}, 500)
