from sqlalchemy.ext.asyncio import async_sessionmaker
from config import ASYNC_ENGINE


FASTAPI_ASYNC_SESSIONMAKER = async_sessionmaker(ASYNC_ENGINE)
"Специализированная для FastAPI асинхронная фабрика сессий БД. При вызове создает сессию"
