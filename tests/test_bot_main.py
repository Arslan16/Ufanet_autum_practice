import asyncio
import pytest
import contextlib

from unittest.mock import AsyncMock, patch

from factories import card_factory, my_hypothesis_settings, queue_factory
from hypothesis import given, settings
from bot_main import bot, rmq_manager, main


@pytest.mark.asyncio
@given(
    queue_name=queue_factory(),
    payload=card_factory()
)
@settings(**my_hypothesis_settings)
async def test_run_listening_queue(
    queue_name: str,
    payload: dict):
    with patch.object(bot, "send_message", new_callable=AsyncMock) as mock_send, \
        patch("bot_main.FASTAPI_DATABASE_QUERIES_QUEUE_NAME", queue_name):

        async def limited_run():
            await rmq_manager.drop_queue(queue_name, False, False)
            task = asyncio.create_task(main())
            success = await rmq_manager.send_message_to_queue(
                queue_name, 
                payload
            )
            assert success is True
            await asyncio.sleep(5)
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task

        await limited_run()

    mock_send.assert_awaited_once()

