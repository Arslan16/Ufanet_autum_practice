from fastapi import APIRouter, Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from config import TEMPLATES, PROJECT_NAME
from ..dependencies import async_session_generator

client_rt = APIRouter()


@client_rt.get("/partnerprogram")
async def partnerprogram_get_handler(request: Request, session: AsyncSession = Depends(async_session_generator)):
    "Обработчик который будет выводить страничку со списоком категорий"
    return TEMPLATES.TemplateResponse(request, "client/partnerprogram.html", {"base_path": f"{PROJECT_NAME}"})

