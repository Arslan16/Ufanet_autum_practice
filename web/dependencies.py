from collections.abc import AsyncGenerator
from typing import Any

from .config import FASTAPI_ASYNC_SESSIONMAKER


async def async_session_generator() -> AsyncGenerator[Any, Any]:
    "Генератор сессии с базой данных. Одна сессия на 1 запрос"
    async with FASTAPI_ASYNC_SESSIONMAKER() as session:
        yield session

