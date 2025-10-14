import asyncio
import pytest
import contextlib

from unittest.mock import AsyncMock, patch

from factories import card_factory, my_hypothesis_settings, queue_factory
from hypothesis import given, settings
from bot_main import RABBIT_MQ_CREDINTAILS, bot, run_listening_queue
from outbox_main import send_message_to_queue


@pytest.mark.asyncio
@given(
    queue_name=queue_factory(),
    payload=card_factory()
)
@settings(**my_hypothesis_settings)
async def test_run_listening_queue(
    queue_name: str,
    payload: dict):
    # Отправляем сообщение в очередь через реальную функцию
    success = await send_message_to_queue(queue_name, payload, RABBIT_MQ_CREDINTAILS, durable=False)
    assert success is True

    # Мокаем bot.send_message
    with patch.object(bot, "send_message", new_callable=AsyncMock) as mock_send:
        async def limited_run():
            task = asyncio.create_task(run_listening_queue(queue_name, RABBIT_MQ_CREDINTAILS, durable=False))
            await asyncio.sleep(2)  # Ждём, пока сообщение обработается
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task

        await limited_run()

    # Проверяем, что bot.send_message вызвался с нашим payload
    mock_send.assert_awaited_once()

