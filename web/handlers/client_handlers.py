from fastapi import APIRouter, Request, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any
from loguru import logger

from config import TEMPLATES
from core.database_utils import get_all_categories, get_all_cards_in_category_with_short_description, get_card_info_by_card_id
from ..dependencies import async_session_generator
from ..schemas import CardPydanticModel


client_rt = APIRouter(prefix="/partnerprogram")
"Роутер отвечающий за обработку запросов для обычного посетителя сайта(Клиента)"


@client_rt.get("/")
async def partnerprogram_get_handler(request: Request, session: AsyncSession = Depends(async_session_generator)):
    "Обработчик который будет выводить страничку со списоком категорий"
    categories: list[dict[str, Any]] = await get_all_categories(session)
    logger.debug(f"{categories=}")
    return TEMPLATES.TemplateResponse(request, "client/partnerprogram.html", {"categories": categories})


@client_rt.get("/cards")
async def partnerprogram_cards_post_handler(request: Request, category_id: int | None = Query(None), session: AsyncSession = Depends(async_session_generator)):
    "Обработчик который выводит страничку со списком карточек в определенной категории, определяемой по category_id"
    if isinstance(category_id, int):
        cards: list[dict] = await get_all_cards_in_category_with_short_description(category_id, session)
    else:
        cards = list()
    logger.debug(f"{cards=}")
    return TEMPLATES.TemplateResponse(request, "client/cards.html", {"cards": cards})


@client_rt.post("/cards/get_card_info")
async def get_card_info_post_handler(request: Request, data: CardPydanticModel, session: AsyncSession = Depends(async_session_generator)):
    card_info: dict[str, Any] = await get_card_info_by_card_id(data.card_id, session)
    logger.debug(f"{card_info=}")
    return TEMPLATES.TemplateResponse(request, "client/cards_modal.html", {"card": card_info})

