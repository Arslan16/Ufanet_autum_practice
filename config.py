import os
from sqlalchemy import URL
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from dotenv import load_dotenv, dotenv_values as get_dotenv_values
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles


load_dotenv()
dotenv_values = get_dotenv_values()

CURRENT_DIR: str = str(os.path.dirname(os.path.abspath(__file__)))
"Абсолютный путь к текущей папке"

PROJECT_NAME: str = (CURRENT_DIR).split("/" if "/" in CURRENT_DIR else "\\")[-1]
"Имя проекта(Текущая папка) для создания веб путей (root_path)"

ASYNC_ENGINE: AsyncEngine = create_async_engine(
    URL.create(
        host="localhost",
        drivername="postgresql+asyncpg",
        username=dotenv_values.get("DATABASE_USERNAME", "postgres"),
        password=dotenv_values.get("DATABASE_PASSWORD", "postgres"),
        database=dotenv_values.get("DATABASE_NAME"),
        port=int(dotenv_values.get("DATABASE_PORT", 5432))
    )
)
"Асинхронный движок для соединения с базой данных"

STATIC_FILES: StaticFiles  = StaticFiles(directory=os.path.join(f"{CURRENT_DIR}/web", "static"))
"Путь к папке, в которой лежат статичные файлы(css/js)"

TEMPLATES: Jinja2Templates = Jinja2Templates(directory=os.path.join(f"{CURRENT_DIR}/web", "templates"))
"Путь к папке, в которой лежат шаблоны страниц(html)"

HOST: str = dotenv_values.get("HOST", "localhost")
"Хост на котором будет запускаться FastAPI, по умолчанию 'localhost'"

PORT: int = int(dotenv_values.get("PORT", 8000))
"Порт на котором будет запускаться FastAPI, по умолчанию 8000"
