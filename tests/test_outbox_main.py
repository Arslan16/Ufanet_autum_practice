import pytest
import asyncio

from contextlib import asynccontextmanager
from unittest.mock import ANY, AsyncMock, call, patch

from hypothesis import given, settings
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.core_types import OutBoxStatuses
from core.database_utils import (
    insert_into_outbox,
    get_last_pending_messages_from_outbox,
    set_status_of_outbox_row
)
from core.models import BaseTable, OutboxTable
from outbox.config import RABBIT_MQ_CREDINTAILS
from outbox_main import run_outbox_table_polling
from tests.factories import card_factory, engine, my_hypothesis_settings, queue_factory, test_async_session_maker


@pytest.fixture(scope="function")
async def session():
    async with engine.begin() as conn:
        await conn.run_sync(BaseTable().metadata.drop_all)
        await conn.run_sync(BaseTable().metadata.create_all)

    async with test_async_session_maker() as session:
        yield session

    await engine.dispose()


@pytest.fixture(autouse=True)
async def clear_db(session):
    loop = asyncio.get_running_loop()
    for table in reversed(BaseTable.metadata.sorted_tables):
        await loop.run_in_executor(None, lambda: session.execute(table.delete()))
    await session.commit()


@pytest.fixture(autouse=True)
async def cleanup_session(session: AsyncSession):
    yield
    await session.rollback()


@asynccontextmanager
async def fake_session_maker():
    async with test_async_session_maker() as my_session:
        yield my_session


@pytest.mark.asyncio
@given(
    queue_name=queue_factory(),
    payload=card_factory()
)
@settings(**my_hypothesis_settings)
async def test_run_outbox_table_polling(
    monkeypatch: pytest.MonkeyPatch,
    session: AsyncSession,
    queue_name: str,
    payload: dict
):
    await insert_into_outbox(
        payload=payload,
        queue=queue_name,
        session=session
    )
    await session.commit()
    monkeypatch.setattr("outbox_main.OUTBOX_ASYNC_SESSIONMAKER", fake_session_maker)

    with patch("outbox_main.set_status_of_outbox_row", new_callable=AsyncMock) as mock_set:
        await run_outbox_table_polling(
            queue_name,
            RABBIT_MQ_CREDINTAILS,
            iterations=1
        )

        sent_calls = [
            call(1, OutBoxStatuses.SENT, ANY)
        ]
        mock_set.assert_has_awaits(sent_calls)


@pytest.mark.asyncio
@given(
    queue_name=queue_factory(),
    payload=card_factory()
)
@settings(**my_hypothesis_settings)
async def test_get_last_pending_messages_from_outbox(
    session: AsyncSession,
    queue_name: str,
    payload: dict
):
    await insert_into_outbox(
        payload=payload,
        queue=queue_name,
        session=session
    )
    await session.commit()

    result = await get_last_pending_messages_from_outbox(session)
    # Обязательное явное приведение к int чтобы "Отвязать" ID от БД и избежать greenlet_spawn
    row_id = int(result[-1].id)
    assert isinstance(result, list)
    assert len(result) >= 1
    assert result[-1].payload == payload
    assert result[-1].queue == queue_name

    await set_status_of_outbox_row(row_id, OutBoxStatuses.FAILED, session)
    stmt = select(OutboxTable).where(OutboxTable.id == row_id)
    upd_outbox_row = await session.scalar(stmt)
    assert isinstance(upd_outbox_row, OutboxTable)
    assert upd_outbox_row.status == OutBoxStatuses.FAILED

