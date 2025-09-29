from fastapi import APIRouter, Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any
from loguru import logger

from config import TEMPLATES, PROJECT_NAME
from core.database_utils import get_all_categories_as_list_of_dict
from ..dependencies import async_session_generator


client_rt = APIRouter(prefix="/partnerprogram")


@client_rt.get("/")
async def partnerprogram_get_handler(request: Request, session: AsyncSession = Depends(async_session_generator)):
    "Обработчик который будет выводить страничку со списоком категорий"
    categories: list[dict[str, Any]] = await get_all_categories_as_list_of_dict(session)
    logger.info(f"{categories=}")
    return TEMPLATES.TemplateResponse(request, "client/partnerprogram.html", {"base_path": f"{PROJECT_NAME}", "categories": categories})


@client_rt.get("/cards")
async def partnerprogram_cards_get_handler(request: Request, session: AsyncSession = Depends(async_session_generator)):
    ...