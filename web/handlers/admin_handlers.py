from fastapi import APIRouter, Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any
from loguru import logger

from config import TEMPLATES
from core.models import BaseTable, CardsTable, CompaniesTable, CategoriesTable, dict_tables
from core.database_utils import get_all_rows_from_table
from ..dependencies import async_session_generator
from ..schemas import GetTableDataModel


admin_rt = APIRouter(prefix="/admin")
"Роутер отвечающий за обработку запросов для администратора"


@admin_rt.get("/")
async def index_get_handler(request: Request):
    return TEMPLATES.TemplateResponse(request, "admin/index.html", {"tables": {"Комании": CompaniesTable.__tablename__, "Карточки": CardsTable.__tablename__, "Категории": CategoriesTable.__tablename__}})


@admin_rt.post("/get_table_data")
async def get_table_data(request: Request, data: GetTableDataModel, session: AsyncSession = Depends(async_session_generator)):
    if dict_tables.get(data.tablename) is not None:
        table: BaseTable = dict_tables.get(data.tablename)
        rows: list[dict[str, Any]] = await get_all_rows_from_table(table, session)
        logger.debug(f"{rows=}")
        return TEMPLATES.TemplateResponse(request, "admin/table.html", {"columns": [column.name for column in table.__table__.columns], "rows": rows})


