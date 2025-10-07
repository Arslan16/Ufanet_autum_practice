from typing import Any

from fastapi import APIRouter, Depends, Query, Request
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from core.database_utils import (
    get_all_cards_in_category_with_short_description,
    get_all_categories,
    get_card_info_by_card_id,
)

from ..config import FASTAPI_DATABASE_QUERIES_QUEUE_NAME, TEMPLATES
from ..dependencies import async_session_generator
from ..schemas import CardPydanticModel

client_rt = APIRouter(prefix="/partnerprogram")
"Роутер отвечающий за обработку запросов для обычного посетителя сайта(Клиента)"


@client_rt.get("/")
async def partnerprogram_get_handler(
    request: Request,
    session: AsyncSession = Depends(async_session_generator)
):
    """
    Обрабатывает GET-запрос для отображения страницы с партнерской программой и списком категорий.

    Функция:
    - Извлекает все категории из базы данных в виде списка словарей;
    - Логирует полученные данные для отладки;
    - Передаёт данные в Jinja-шаблон для формирования HTML-страницы с категориями.

    Args:
        request (Request): Текущий HTTP-запрос (FastAPI).
        session (AsyncSession): Асинхронная сессия SQLAlchemy для работы с БД.

    Returns:
        TemplateResponse: HTML-страница с партнерской программой, включающая:
            - список категорий (`categories`) в формате list[dict].
    """
    categories: list[dict[str, Any]] = await get_all_categories(session, FASTAPI_DATABASE_QUERIES_QUEUE_NAME)
    "Список словарей отражающих запись в бд о категории по принципу ключ:столбец значение:значение"
    logger.debug(f"{categories=}")
    return TEMPLATES.TemplateResponse(request, "client/partnerprogram.html", {"categories": categories})


@client_rt.get("/cards")
async def partnerprogram_cards_post_handler(
    request: Request,
    category_id: int | None = Query(None),
    session: AsyncSession = Depends(async_session_generator)
):
    """
    Обрабатывает GET-запрос для отображения страницы с карточками в определённой категории.

    Функция:
    - Проверяет наличие и корректность параметра `category_id`;
    - Если `category_id` указан, извлекает все карточки в данной категории с кратким описанием;
    - Если `category_id` отсутствует или некорректен, возвращает пустой список;
    - Передаёт данные в Jinja-шаблон для формирования HTML-страницы с карточками.

    Args:
        request (Request): Текущий HTTP-запрос (FastAPI).
        category_id (int | None): Идентификатор категории карточек (опционально, через query-параметр).
        session (AsyncSession): Асинхронная сессия SQLAlchemy для работы с БД.

    Returns:
        TemplateResponse: HTML-страница со списком карточек, включающая:
            - список карточек (`cards`) в формате list[dict].
    """
    if isinstance(category_id, int):
        cards: list[dict] = await get_all_cards_in_category_with_short_description(
            category_id=category_id,
            session=session,
            queue_name=FASTAPI_DATABASE_QUERIES_QUEUE_NAME)
        "Список словарей отражающих запись в бд о карточке по принципу ключ:столбец значение:значение"
    else:
        cards = list()
        "Пустой список если category_id не число"
    logger.debug(f"{cards=}")
    return TEMPLATES.TemplateResponse(request, "client/cards.html", {"cards": cards})


@client_rt.post("/cards/get_card_info")
async def get_card_info_post_handler(
    request: Request,
    data: CardPydanticModel,
    session: AsyncSession = Depends(async_session_generator)
):
    """
    Обрабатывает POST-запрос на получение детальной информации
    о карточке и формирует HTML для модального окна.

    Функция:
    - Извлекает данные о карточке из базы по `card_id`;
    - Логирует полученную информацию для отладки;
    - Передаёт данные в Jinja-шаблон для формирования содержимого модального окна.

    Args:
        request (Request): Текущий HTTP-запрос (FastAPI).
        data (CardPydanticModel): Pydantic-модель с идентификатором карточки (`card_id`).
        session (AsyncSession): Асинхронная сессия SQLAlchemy для работы с БД.

    Returns:
        TemplateResponse: HTML-фрагмент модального окна с детальной информацией о карточке (`card`).
    """
    card_info: dict[str, Any] = await get_card_info_by_card_id(
        card_id=data.card_id,
        session=session,
        queue_name=FASTAPI_DATABASE_QUERIES_QUEUE_NAME
    )
    "Словарь с информацией о конкретной карточке извлеченной по ее id в бд"
    logger.debug(f"{card_info=}")
    return TEMPLATES.TemplateResponse(request, "client/modal.html", {"card": card_info})

