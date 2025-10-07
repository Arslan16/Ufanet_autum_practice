import json

from core.types import RabbitMQCredentials
from dotenv import dotenv_values as get_dotenv_values
from dotenv import load_dotenv
from sqlalchemy import URL
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine

# Загрузка переменных окружения .env
load_dotenv()

dotenv_values: dict[str, str] = get_dotenv_values()
"Переменные окружения .env"

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

RMQ_HOST: str = dotenv_values.get("RMQ_HOST", "127.0.0.1")
"Хост на котором запущен RabbitMQ"

RMQ_PORT: int = int(dotenv_values.get("RMQ_PORT"))
"Порт на котором запущен RabbitMQ"

RMQ_LOGIN: str = dotenv_values.get("RMQ_LOGIN")
"Логин пользователя RabbitMQ"

RMQ_PASSWORD: str = dotenv_values.get("RMQ_PASSWORD")
"Пароль пользователя RabbitMQ"

BOT_ASYNC_SESSIONMAKER = async_sessionmaker(ASYNC_ENGINE, expire_on_commit=False)
"Специализированная для сервиса OUTBOX асинхронная фабрика сессий БД. При вызове создает сессию"

RABBIT_MQ_CREDINTAILS: RabbitMQCredentials = RabbitMQCredentials(
    host=RMQ_HOST,
    port=RMQ_PORT,
    login=RMQ_LOGIN,
    password=RMQ_PASSWORD
)
"Аутентификационные данные для подключения к RabbitMQ для сайта(publisher)"

FASTAPI_DATABASE_QUERIES_QUEUE_NAME = "database_queries"
"Имя очереди в которую надо публиковать сообщения о совершенных запросах"

BOT_TOKEN: str = dotenv_values.get("BOT_TOKEN")
"Токен телеграм бота для отправки информации о запросах админу"

