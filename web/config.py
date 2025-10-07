import json
from pathlib import Path

from dotenv import dotenv_values as get_dotenv_values
from dotenv import load_dotenv
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import URL
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine

# Загрузка переменных окружения .env
load_dotenv()

dotenv_values: dict[str, str | None] = get_dotenv_values()
"Переменные окружения .env"

CURRENT_DIR: Path = Path(__file__).resolve().parent
"Абсолютный путь к текущей папке"

PROJECT_NAME: str = "Ufanet_autum_practice"
"Имя проекта для создания веб путей (root_path)"

ASYNC_ENGINE: AsyncEngine = create_async_engine(
    URL.create(
        host=dotenv_values.get("DATABASE_HOST", "localhost"),
        drivername="postgresql+asyncpg",
        username=dotenv_values.get("DATABASE_USERNAME", "postgres"),
        password=dotenv_values.get("DATABASE_PASSWORD", "postgres"),
        database=dotenv_values.get("DATABASE_NAME"),
        port=int(dotenv_values.get("DATABASE_PORT", 5432))
    ),
    pool_pre_ping=True,
    json_serializer=lambda obj: json.dumps(obj, ensure_ascii=False)
)
"Асинхронный движок для соединения с базой данных"

STATIC_FILES: StaticFiles  = StaticFiles(directory=CURRENT_DIR / "static")
"Путь к папке, в которой лежат статичные файлы(css/js)"

TEMPLATES: Jinja2Templates = Jinja2Templates(directory=CURRENT_DIR / "templates")
"Путь к папке, в которой лежат шаблоны страниц(html)"

HOST: str = dotenv_values.get("HOST", "localhost")
"Хост на котором будет запускаться FastAPI, по умолчанию 'localhost'"

PORT: int = int(dotenv_values.get("PORT", 8000))
"Порт на котором будет запускаться FastAPI, по умолчанию 8000"

FASTAPI_ASYNC_SESSIONMAKER = async_sessionmaker(ASYNC_ENGINE, expire_on_commit=False)
"Специализированная для FastAPI асинхронная фабрика сессий БД. При вызове создает сессию"

FASTAPI_DATABASE_QUERIES_QUEUE_NAME = "database_queries"
"Имя очереди в которую надо публиковать сообщения о совершенных запросах"

