import json
from pathlib import Path
from sqlalchemy import URL
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from dotenv import load_dotenv, dotenv_values as get_dotenv_values
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles


# Загрузка переменных окружения .env
load_dotenv()

dotenv_values: dict[str, str] = get_dotenv_values()
"Переменные окружения .env"

CURRENT_DIR: Path = Path(__file__).resolve().parent
"Абсолютный путь к текущей папке"

PROJECT_NAME: str = CURRENT_DIR.name
"Имя проекта(Текущая папка) для создания веб путей (root_path)"

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

STATIC_FILES: StaticFiles  = StaticFiles(directory=CURRENT_DIR / "web" / "static")
"Путь к папке, в которой лежат статичные файлы(css/js)"

TEMPLATES: Jinja2Templates = Jinja2Templates(directory=CURRENT_DIR / "web" / "templates")
"Путь к папке, в которой лежат шаблоны страниц(html)"

HOST: str = dotenv_values.get("HOST", "localhost")
"Хост на котором будет запускаться FastAPI, по умолчанию 'localhost'"

PORT: int = int(dotenv_values.get("PORT", 8000))
"Порт на котором будет запускаться FastAPI, по умолчанию 8000"

RMQ_HOST: str = dotenv_values.get("RMQ_HOST", "127.0.0.1")
"Хост на котором запущен RabbitMQ"

RMQ_PORT: int = int(dotenv_values.get("RMQ_PORT"))
"Порт на котором запущен RabbitMQ"

RMQ_LOGIN: str = dotenv_values.get("RMQ_LOGIN")
"Логин пользователя RabbitMQ"

RMQ_PASSWORD: str = dotenv_values.get("RMQ_PASSWORD")
"Пароль пользователя RabbitMQ"

