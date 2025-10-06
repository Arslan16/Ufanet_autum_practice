from sqlalchemy.ext.asyncio import async_sessionmaker

from core.types import RabbitMQCredentials
from config import ASYNC_ENGINE, RMQ_HOST, RMQ_PORT, RMQ_LOGIN, RMQ_PASSWORD


FASTAPI_ASYNC_SESSIONMAKER = async_sessionmaker(ASYNC_ENGINE, expire_on_commit=False)
"Специализированная для FastAPI асинхронная фабрика сессий БД. При вызове создает сессию"

FASTAPI_RABBIT_MQ_CREDINTAILS: RabbitMQCredentials = RabbitMQCredentials(
    host=RMQ_HOST,
    port=RMQ_PORT,
    login=RMQ_LOGIN,
    password=RMQ_PASSWORD
)
"Аутентификационные данные для подключения к RabbitMQ для сайта(publisher)"

FASTAPI_DATABASE_QUERIES_QUEUE_NAME = "database_queries"
"Имя очереди в которую надо публиковать сообщения о совершенных запросах"

