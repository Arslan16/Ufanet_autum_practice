import asyncio
import json
import aio_pika

from aiogram import Bot
from loguru import logger

from bot.config import (
    BOT_TOKEN,
    FASTAPI_DATABASE_QUERIES_QUEUE_NAME, 
    RABBIT_MQ_CREDINTAILS
)
from core.core_types import RabbitMQManager


bot = Bot(BOT_TOKEN)
"Главный объект aiogram - экземпляр телеграм бота с его токеном"

admins: list[int] = [959434557]
"Список telegram id тех кому будут отправляться уведомления"

rmq_manager = RabbitMQManager(RABBIT_MQ_CREDINTAILS)
"Объект управляющй соединением с RabbitMQ"


async def on_message(message: aio_pika.IncomingMessage):
    try:
        async with message.process():
            body = json.loads(message.body)
            for admin in admins:
                try:
                    await bot.send_message(admin, f"```json\n{body}\n```", parse_mode="MarkdownV2")
                except Exception as e:
                    # Ловим сетевые ошибки отправки телеграм
                    logger.error(f"Ошибка отправки в телеграм: {e}")
    except asyncio.CancelledError:
        # Фоновые таски могут быть отменены при shutdown loop
        logger.warning("Callback on_message был отменён")
    except Exception as e:
        # Любые другие ошибки при обработке сообщения
        logger.error(f"Ошибка при обработке RMQ сообщения: {e}")


async def main():
    await rmq_manager.connect()
    await rmq_manager.register_callback_on_queue(
        queue_name=FASTAPI_DATABASE_QUERIES_QUEUE_NAME,
        callback=on_message
    )

    try:
        await asyncio.Event().wait()  # держим loop открытым
    finally:
        await rmq_manager.close()


if __name__ == "__main__":
    asyncio.run(main())
