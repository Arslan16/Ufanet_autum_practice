from fastapi import APIRouter, Request, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any
from loguru import logger

from config import TEMPLATES, PROJECT_NAME
from core.database_utils import get_all_categories, get_all_cards_in_category_with_short_description
from ..dependencies import async_session_generator


client_rt = APIRouter(prefix="/partnerprogram")


@client_rt.get("/")
async def partnerprogram_get_handler(request: Request, session: AsyncSession = Depends(async_session_generator)):
    "Обработчик который будет выводить страничку со списоком категорий"
    categories: list[dict[str, Any]] = await get_all_categories(session)
    logger.info(f"{categories=}")
    return TEMPLATES.TemplateResponse(request, "client/partnerprogram.html", {"base_path": f"{PROJECT_NAME}", "categories": categories})


@client_rt.get("/cards")
async def partnerprogram_cards_post_handler(request: Request, category_id: int | None = Query(None), session: AsyncSession = Depends(async_session_generator)):
    if isinstance(category_id, int):
        cards: list[dict] = await get_all_cards_in_category_with_short_description(category_id, session)
    else:
        cards = list()
    logger.info(f"{cards=}")
    return TEMPLATES.TemplateResponse(request, "client/cards.html", {"cards": cards})
