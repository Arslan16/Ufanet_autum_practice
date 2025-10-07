from fastapi import APIRouter, Request, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any
from loguru import logger

from core.models import BaseTable, CardsTable, CompaniesTable, CategoriesTable, tables, russian_field_names
from core.database_utils import delete_row, get_all_rows_from_table, get_full_row_for_admin_by_id, update_row_by_id, create_row
from web.utils import map_columns_to_table_types
from ..dependencies import async_session_generator
from ..schemas import DeleteRowModel, GetTableDataModel, GetTableRowModel, SaveRowModel, CreateRowGetModalModel, CreateRowModel
from ..config import FASTAPI_DATABASE_QUERIES_QUEUE_NAME, TEMPLATES


admin_rt = APIRouter(prefix="/admin")
"Роутер отвечающий за обработку запросов для администратора"


@admin_rt.get("/")
async def index_get_handler(request: Request):
    """
    Обрабатывает GET-запрос на стартовую страницу админ-панели и формирует HTML со списком таблиц.

    Функция:
    - Определяет доступные таблицы базы данных;
    - Передаёт данные в Jinja-шаблон для формирования HTML-страницы с перечнем таблиц.

    Args:
        request (Request): Текущий HTTP-запрос (FastAPI).

    Returns:
        TemplateResponse: HTML-страница админ-панели со списком таблиц базы данных (`tables`), где ключи — читаемые названия таблиц, а значения — их имена в базе данных.
    """
    return TEMPLATES.TemplateResponse(request, "admin/index.html", {"tables": {"Комании": CompaniesTable.__tablename__, "Карточки": CardsTable.__tablename__, "Категории": CategoriesTable.__tablename__}})


@admin_rt.post("/get_table_data")
async def get_table_data(request: Request, data: GetTableDataModel, session: AsyncSession = Depends(async_session_generator)):
    """
    Обрабатывает POST-запрос на получение данных таблицы из базы и отрисовку их в HTML-шаблоне.

    Функция:
    - Определяет модель таблицы по её имени (`data.tablename`);
    - Извлекает все записи из этой таблицы в виде списка словарей;
    - Передаёт данные в Jinja-шаблон для формирования HTML-фрагмента с таблицей.

    Args:
        request (Request): Текущий HTTP-запрос (FastAPI).
        data (GetTableDataModel): Pydantic-модель с именем таблицы.
        session (AsyncSession): Асинхронная сессия SQLAlchemy для работы с БД.

    Returns:
        TemplateResponse: HTML-страница (или часть страницы) с таблицей, включающей:
            - название таблицы;
            - список названий колонок;
            - словарь русских описаний полей (`descriptions`);
            - строки данных в формате list[dict].
    """
    if tables.get(data.tablename) is not None:
        table: BaseTable = tables.get(data.tablename)
        "Модель таблицы базы данных извлеченная по ее названию"
        
        rows: list[dict[str, Any]] = await get_all_rows_from_table(table, session, FASTAPI_DATABASE_QUERIES_QUEUE_NAME)
        "Список словарей отражающих запись в базе данных по принципу ключ:столбец значение:значение столбца"
        
        logger.debug(f"{rows=}")
        return TEMPLATES.TemplateResponse(request, "admin/table.html", {"tablename": data.tablename, "columns": [column.name for column in table.__table__.columns], "descriptions": russian_field_names, "rows": rows})


@admin_rt.post("/get_table_row")
async def get_table_row_post_handler(request: Request, data: GetTableRowModel, session: AsyncSession = Depends(async_session_generator)):
    """
    Обрабатывает POST-запрос на получение данных конкретной строки таблицы и формирование модального окна для редактирования.

    Функция:
    - Определяет модель таблицы по её имени (`data.tablename`);
    - Извлекает запись из базы данных по её идентификатору (`data.id`);
    - Передаёт данные в Jinja-шаблон для отрисовки HTML-модального окна с подробной информацией.

    Args:
        request (Request): Текущий HTTP-запрос (FastAPI).
        data (GetTableRowModel): Pydantic-модель с именем таблицы и идентификатором записи.
        session (AsyncSession): Асинхронная сессия SQLAlchemy для работы с БД.

    Returns:
        TemplateResponse: HTML-фрагмент модального окна с:
            - идентификатором записи;
            - данными строки в формате dict;
            - словарём русских описаний полей (`descriptions`);
            - списком колонок для отображения.
    """

    if tables.get(data.tablename) is not None:
        table: BaseTable = tables.get(data.tablename)
        row_info: dict[str, Any] = await get_full_row_for_admin_by_id(data.id, table, session)
        "Информация о конкретной карточке извлеченной по ее ид, содержащая полуню информацию о ней для редактирования админом"
        logger.debug(f"{row_info=}")
        return TEMPLATES.TemplateResponse(request, "admin/modal_save.html", {"row_id": data.id, "row_info": row_info, "descriptions": russian_field_names, "columns": row_info.keys()})


@admin_rt.post("/save_row")
async def save_row_post_handler(data: SaveRowModel, session: AsyncSession = Depends(async_session_generator)):
    """
    Обрабатывает POST-запрос на сохранение (обновление) данных конкретной строки таблицы.

    Функция:
    - Определяет модель таблицы по её имени (`data.tablename`);
    - Приводит данные к типам, соответствующим столбцам таблицы;
    - Обновляет запись в базе данных по её идентификатору (`data.id`);
    - Возвращает результат операции в формате JSON.

    Args:
        data (SaveRowModel): Pydantic-модель с именем таблицы, идентификатором строки и словарём новых данных.
        session (AsyncSession): Асинхронная сессия SQLAlchemy для работы с БД.

    Returns:
        JSONResponse: 
            - `{"ok": True}` с кодом 200 при успешном обновлении;
            - `{"ok": False, "error": str}` с кодом 500 при ошибке обновления.
    """

    if tables.get(data.tablename) is not None:
        table: BaseTable = tables.get(data.tablename)
        normalized_data: dict[str, Any] = map_columns_to_table_types(table, data.data)
        update_res: bool | str = await update_row_by_id(data.id, table, normalized_data, session, FASTAPI_DATABASE_QUERIES_QUEUE_NAME)
        if update_res is True:
            return JSONResponse({"ok": True}, 200)
        else:
            return JSONResponse({"ok": False, "error": update_res}, 500)


@admin_rt.post("/get_modal_to_create_row")
async def create_row_get_handler(request: Request, data: CreateRowGetModalModel):
    """
    Обрабатывает POST-запрос на получение HTML-шаблона модального окна для создания новой записи в таблице.

    Функция:
    - Определяет модель таблицы по её имени (`data.tablename`);
    - Извлекает список колонок таблицы;
    - Передаёт данные в Jinja-шаблон для формирования модального окна с полями для ввода новых данных.

    Args:
        request (Request): Текущий HTTP-запрос (FastAPI).
        data (CreateRowGetModalModel): Pydantic-модель с именем таблицы.

    Returns:
        TemplateResponse: HTML-фрагмент модального окна с:
            - полями ввода для каждой колонки таблицы;
            - словарём русских описаний полей (`descriptions`);
            - список названий колонок (`columns`).
    """

    if tables.get(data.tablename) is not None:
        table: BaseTable = tables.get(data.tablename)
        columns: list[str] = [column.name for column in table.__table__.columns]
        "Список названий столбцов таблицы"
        logger.debug(f"{columns=}")
        return TEMPLATES.TemplateResponse(request, "admin/modal_create.html", {"descriptions": russian_field_names, "columns": columns})


@admin_rt.post("/create_row")
async def create_row_post_handler(data: CreateRowModel, session: AsyncSession = Depends(async_session_generator)):
    """
    Обрабатывает POST-запрос на создание новой записи в указанной таблице.

    Функция:
    - Определяет модель таблицы по её имени (`data.tablename`);
    - Преобразует переданные данные к типам столбцов таблицы;
    - Создаёт новую запись в базе данных;
    - Возвращает JSON-ответ с результатом операции.

    Args:
        data (CreateRowModel): Pydantic-модель с именем таблицы и данными новой записи.
        session (AsyncSession): Асинхронная сессия SQLAlchemy для работы с БД.

    Returns:
        JSONResponse: Объект JSON с результатом создания записи:
            - `{"ok": True, "id": new_id}` — если запись успешно создана;
            - `{"ok": False, "error": error_message}` — если произошла ошибка.
    """
    if tables.get(data.tablename) is not None:
        table: BaseTable = tables.get(data.tablename)
        normalized_data: dict[str, Any] = map_columns_to_table_types(table, data.data)
        new_id: int | str = await create_row(table, normalized_data, session, FASTAPI_DATABASE_QUERIES_QUEUE_NAME)
        if isinstance(new_id, int):
            return JSONResponse({"ok": True, "id": new_id}, 200)
        else:
            return JSONResponse({"ok": False, "error": new_id}, 500)


@admin_rt.post("/delete_row")
async def create_row_post_handler(data: DeleteRowModel, session: AsyncSession = Depends(async_session_generator)):
    """
    Обрабатывает POST-запрос на удаление записи из указанной таблицы.

    Функция:
    - Определяет модель таблицы по её имени (`data.tablename`);
    - Удаляет запись с указанным идентификатором (`data.id`) из базы данных;
    - Возвращает JSON-ответ с результатом операции.

    Args:
        data (DeleteRowModel): Pydantic-модель с именем таблицы и ID записи для удаления.
        session (AsyncSession): Асинхронная сессия SQLAlchemy для работы с БД.

    Returns:
        JSONResponse: Объект JSON с результатом удаления:
            - `{"ok": True}` — если запись успешно удалена;
            - `{"ok": False, "error": error_message}` — если произошла ошибка.
    """

    if tables.get(data.tablename) is not None:
        table: BaseTable = tables.get(data.tablename)
        del_res = await delete_row(data.id, table, session, FASTAPI_DATABASE_QUERIES_QUEUE_NAME)
        if del_res is True:
            return JSONResponse({"ok": True}, 200)
        else:
            return JSONResponse({"ok": False, "error": del_res}, 500)
