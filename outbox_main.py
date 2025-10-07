import json
import asyncio

from loguru import logger

from core.database_utils import get_last_pending_messages_from_outbox, set_status_of_outbox_row
from core.rmq_utils import send_message_to_queue
from core.types import OutBoxStatuses
from outbox.config import OUTBOX_ASYNC_SESSIONMAKER, RABBIT_MQ_CREDINTAILS, FASTAPI_DATABASE_QUERIES_QUEUE_NAME


async def run_outbox_table_polling():
    """
    Запускает переодический просмотр таблицы outbox на наличие новых сообщений

    Функция:
    
    - Каждые 3 секунды извлекает записи из таблицы `outbox` с статусом `PENDING`;
    - Отправляет сообщение в брокер сообщений;
    - Если запись успешно отправлена то помечает запись как `SENT` иначе `FAILED`.
    
    """
    logger.info("Работа outbox процессора начата!")
    async with OUTBOX_ASYNC_SESSIONMAKER() as session:
        while True:
            last_msgs = await get_last_pending_messages_from_outbox(session)
            for message in last_msgs:
                status = await send_message_to_queue(
                    queue_name=FASTAPI_DATABASE_QUERIES_QUEUE_NAME, 
                    message=json.dumps(message.payload),
                    credintails=RABBIT_MQ_CREDINTAILS
                )
                if status:
                    await set_status_of_outbox_row(message.id, OutBoxStatuses.SENT, session)
                else:
                    await set_status_of_outbox_row(message.id, OutBoxStatuses.FAILED, session)
            await asyncio.sleep(3)


if __name__ == "__main__":
    try:
        asyncio.run(run_outbox_table_polling())
    except KeyboardInterrupt:
        logger.info("Работа outbox процессора завершена!")
