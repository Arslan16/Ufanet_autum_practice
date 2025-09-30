import uvicorn
import logging
import sys
from fastapi import FastAPI
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession

from core.models import BaseTable
from web.handlers.client_handlers import client_rt
from web.handlers.test_handlers import test_rt
from config import STATIC_FILES, HOST, PORT, PROJECT_NAME, ASYNC_ENGINE


@asynccontextmanager
async def lifespan(app: FastAPI):
    "Функция которая запускается при старте FastAPI. Создает таблицы в бд и закрывает соединение с ней когда приложение завершает работу"
    async with ASYNC_ENGINE.begin() as conn:
        await conn.run_sync(BaseTable.metadata.create_all)

    yield

    await AsyncSession.close_all()
    await ASYNC_ENGINE.dispose()


app: FastAPI = FastAPI(
    root_path=f"/{PROJECT_NAME}", 
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None,
    openapi_url=None
)
"Главное приложений FastAPI"

app.mount("/static", STATIC_FILES, "static")
app.include_router(client_rt)
app.include_router(test_rt)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
    if HOST == "localhost":
        uvicorn.run(app, host=HOST, port=int(PORT))
    else:
        uvicorn.run(app, host=HOST, port=int(PORT),
            ssl_keyfile=f"/etc/letsencrypt/live/{HOST}/privkey.pem",
            ssl_certfile=f"/etc/letsencrypt/live/{HOST}/fullchain.pem"
        )
