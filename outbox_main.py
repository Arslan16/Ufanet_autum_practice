import asyncio
import json

from loguru import logger

from core.core_types import OutBoxStatuses, RabbitMQCredentials
from core.database_utils import get_last_pending_messages_from_outbox, set_status_of_outbox_row
from core.models import OutboxTable
from core.rmq_utils import send_message_to_queue
from outbox.config import FASTAPI_DATABASE_QUERIES_QUEUE_NAME, OUTBOX_ASYNC_SESSIONMAKER, RABBIT_MQ_CREDINTAILS


async def run_outbox_table_polling(
    queue_name: str,
    credintails: RabbitMQCredentials,
    iterations: int | None = None
):
    """
    Запускает переодический просмотр таблицы outbox на наличие новых сообщений

    Функция:
    - Каждые 3 секунды извлекает записи из таблицы `outbox` с статусом `PENDING`;
    - Отправляет сообщение в брокер сообщений;
    - Если запись успешно отправлена то помечает запись как `SENT` иначе `FAILED`.

    Args:
        queue_name (str): Имя прослушиваемой очереди
        credintails (outbox.config.RabbitMQCredentails): авториазционные данные для rmq
        iterations (int | None): Число запросов в базу данных(Для тестирования, по умолчанию None)
    """
    logger.info("Работа outbox процессора начата!")
    async with OUTBOX_ASYNC_SESSIONMAKER() as session:
        i: int = 0
        while True:
            last_msgs: list[OutboxTable] = await get_last_pending_messages_from_outbox(session)
            "Сообщения со статусом `PENDING` в порядке возрастания по дате"

            for message in last_msgs:
                status = await send_message_to_queue(
                    queue_name=queue_name,
                    message=json.dumps(message.payload),
                    credintails=credintails
                )
                if status:
                    await set_status_of_outbox_row(message.id, OutBoxStatuses.SENT, session)
                else:
                    await set_status_of_outbox_row(message.id, OutBoxStatuses.FAILED, session)

            if isinstance(iterations, int):
                i += 1
                if i >= iterations:
                    break
            await asyncio.sleep(3)


if __name__ == "__main__":
    try:
        asyncio.run(run_outbox_table_polling(
            FASTAPI_DATABASE_QUERIES_QUEUE_NAME,
            RABBIT_MQ_CREDINTAILS
        ))
    except KeyboardInterrupt:
        logger.info("Работа outbox процессора завершена!")
