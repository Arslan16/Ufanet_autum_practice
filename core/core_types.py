import asyncio
import json
import aio_pika

from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable
import aiormq
from loguru import logger


@dataclass
class RabbitMQCredentials:
    """
    Параметры подключеня к RabbitMQ:
    Args:
        host (str): Хост на котором запущено rmq (Например `127.0.0.1`)
        port (int): Порт на котором хостится rmq (Например `5672`)
        login (str): Логин пользователя (Например `guest`)
        password (str): Пароль пользователя (Например `guest`)
    """
    host: str
    port: int
    login: str
    password: str

    def to_connection_params(self) -> dict:
        return {
            "host": self.host,
            "port": self.port,
            "login": self.login,
            "password": self.password,
        }

    def to_url(self) -> str:
        return f"amqp://{self.login}:{self.password}@{self.host}:{self.port}"


class OutBoxStatuses(Enum):
    PENDING = "pending"        # Ожидает отправки
    SENT = "sent"              # Успешно отправлено
    FAILED = "failed"          # Ошибка отправки
    ARCHIVED = "archived"      # Удалено из активной таблицы


class RabbitMQManager:
    """
    Менеджер управления RabbitMQ

    Args:
        credintails (RabbitMQCredentails): Авторизационные данные
    """
    def __init__(self, credintails):
        self.credintails = credintails
        self.connection: aio_pika.RobustConnection | None = None
        self.channel: aio_pika.Channel | None = None

    async def send_message_to_queue(
        self,
        queue_name: str,
        message: str | dict | list | Any,
        durable: bool = True  # Дополнительные параметры
    ) -> bool:
        """
        Отправляет сообщение в RabbitMQ очередь
        Returns:
            bool: True если сообщение отправлено успешно
        """
        connection = None
        try:
            # Подключение
            async with await aio_pika.connect_robust(
                    host=self.credintails.host,
                    port=self.credintails.port,
                    login=self.credintails.login,
                    password=self.credintails.password,
                    loop=asyncio.get_event_loop()
                ) as connection, await connection.channel() as channel:
                # Объявление очереди (опционально, но рекомендуется)
                await channel.declare_queue(queue_name, durable=durable)

                # Отправка сообщения
                await channel.default_exchange.publish(
                    aio_pika.Message(
                        body=json.dumps(message).encode(),
                        delivery_mode=aio_pika.DeliveryMode.PERSISTENT if durable else None
                    ),
                    routing_key=queue_name
                )

                logger.info(f"Message sent to queue '{queue_name}'")
                return True

        except Exception as e:
            logger.error(f"Failed to send message to '{queue_name}': {e}")
            return False

        finally:
            if connection:
                await connection.close()

    async def register_callback_on_queue(
        self,
        queue_name: str,
        callback: Callable,
        durable: bool = True  # Дополнительные параметры
) -> aio_pika.queue.ConsumerTag:
        connection = None
        try:
            async with await aio_pika.connect_robust(
                    host=self.credintails.host,
                    port=self.credintails.port,
                    login=self.credintails.login,
                    password=self.credintails.password,
                    loop=asyncio.get_event_loop()
                ) as connection, await connection.channel() as channel:
                # Объявление очереди (опционально, но рекомендуется)
                queue = await channel.declare_queue(queue_name, durable=durable)
                logger.info(f"Callback {callback.__name__} зарегестрирован на очередь {queue_name}")
                return await queue.consume(callback)
        except Exception as e:
            logger.error(e)
            if connection:
                await connection.close()

    async def connect(self):
        self.connection = await aio_pika.connect_robust(
            host=self.credintails.host,
            port=self.credintails.port,
            login=self.credintails.login,
            password=self.credintails.password
        )
        self.channel = await self.connection.channel()
        return self

    async def register_callback_on_queue(
        self,
        queue_name: str,
        callback: Callable,
        durable: bool = True
    ) -> aio_pika.queue.ConsumerTag:
        if not self.channel:
            raise RuntimeError("Не подключён канал")

        queue = await self.channel.declare_queue(queue_name, durable=durable)
        logger.info(f"Callback {callback.__name__} зарегистрирован на очередь {queue_name}")
        return await queue.consume(callback)

    async def close(self):
        if self.channel and not self.channel.is_closed:
            await self.channel.close()
        if self.connection and not self.connection.is_closed:
            await self.connection.close()

    async def drop_queue(
        self,
        queue_name: str,
        if_unused: bool = True,
        if_empty: bool = True
    ):
        try:
            if self.channel:
                queue = await self.channel.declare_queue(queue_name, passive=True)
                await queue.delete(
                    if_unused=if_unused,
                    if_empty=if_empty
                )
        except aiormq.exceptions.ChannelNotFoundEntity as exc:
            logger.error(exc)
        except Exception as exc:
            logger.error(exc)