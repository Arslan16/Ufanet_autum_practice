import asyncio
import json

import aio_pika
from aiogram import Bot
from loguru import logger

from bot.config import BOT_TOKEN, FASTAPI_DATABASE_QUERIES_QUEUE_NAME, RABBIT_MQ_CREDINTAILS, RabbitMQCredentials

bot = Bot(BOT_TOKEN)
"Главный объект aiogram - экземпляр телеграм бота с его токеном"

admins: list[int] = [959434557]
"Список telegram id тех кому будут отправляться уведомления"


async def run_listening_queue(
    queue_name: str,
    credintails: RabbitMQCredentials,
    durable: bool = True  # Дополнительные параметры
):
    connection = None
    try:
        async with await aio_pika.connect_robust(
                host=credintails.host,
                port=credintails.port,
                login=credintails.login,
                password=credintails.password,
                loop=asyncio.get_event_loop()
            ) as connection, await connection.channel() as channel:
            # Объявление очереди (опционально, но рекомендуется)
            queue = await channel.declare_queue(queue_name, durable=durable)

            async with queue.iterator() as queue_iter:
                # Cancel consuming after __aexit__
                async for message in queue_iter:
                    async with message.process():
                        body = json.loads(message.body)
                        for admin in admins:
                            await bot.send_message(admin, f"```json\n{body}\n```", parse_mode="MarkdownV2")
    except Exception as e:
        logger.error(e)
        if connection:
            await connection.close()


if __name__ == "__main__":
    asyncio.run(
        run_listening_queue(
            FASTAPI_DATABASE_QUERIES_QUEUE_NAME,
            RABBIT_MQ_CREDINTAILS
        )
    )
