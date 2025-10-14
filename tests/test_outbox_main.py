import pytest
from contextlib import asynccontextmanager
from unittest.mock import ANY, AsyncMock, call, patch

from hypothesis import given, settings
from sqlalchemy.ext.asyncio import AsyncSession

from core.core_types import OutBoxStatuses
from core.database_utils import insert_into_outbox
from core.models import BaseTable
from outbox.config import RABBIT_MQ_CREDINTAILS
from outbox_main import run_outbox_table_polling
from tests.factories import card_factory, engine, my_hypothesis_settings, queue_factory
from tests.test_database_utils import test_async_session_maker


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
    for table in reversed(BaseTable.metadata.sorted_tables):
        await session.execute(table.delete())
    await session.commit()


@pytest.fixture(autouse=True)
async def cleanup_session(session: AsyncSession):
    yield
    await session.rollback()


@asynccontextmanager
async def fake_session_maker():
    async with test_async_session_maker() as my_session:  # session — твоя фикстура
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
        session=session,
        commit=True
    )
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



