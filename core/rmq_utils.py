import aio_pika
import asyncio
import json
from typing import Union, Any
from loguru import logger

from .types import RabbitMQCredentials


async def send_message_to_queue(
    queue_name: str, 
    message: Union[str, dict, list, Any],
    credintails: RabbitMQCredentials,
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
                host=credintails.host,
                port=credintails.port,
                login=credintails.login,
                password=credintails.password,
                loop=asyncio.get_event_loop()
            ) as connection:
            
            async with await connection.channel() as channel:
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
            ) as connection:
            
            async with await connection.channel() as channel:
                # Объявление очереди (опционально, но рекомендуется)
                queue = await channel.declare_queue(queue_name, durable=durable)

                async with queue.iterator() as queue_iter:
                    # Cancel consuming after __aexit__
                    async for message in queue_iter:
                        async with message.process():
                            body = json.loads(message.body)
                            print(body)
    except Exception as e:
        logger.error(e)
        if connection:
            await connection.close()
