import pytest
import string
from unittest.mock import AsyncMock, patch
from hypothesis import given, strategies as st, HealthCheck, settings
from sqlalchemy import select, delete, desc, insert
from sqlalchemy.ext.asyncio import (
    AsyncSession, 
    create_async_engine, 
    async_sessionmaker,
    AsyncEngine
)

from core.core_types import OutBoxStatuses
from core.models import (
    BaseTable, 
    CategoriesTable,
    CompaniesTable, 
    OutboxTable,
    CardsTable
)
from core.database_utils import (
    create_row,
    get_all_cards_in_category_with_short_description,
    insert_into_outbox,
    get_all_categories,
    get_last_pending_messages_from_outbox,
    set_status_of_outbox_row
)


@pytest.fixture(scope="function")
async def session():
    engine: AsyncEngine = create_async_engine(
        f"postgresql+asyncpg://postgres:postgres@localhost/ufanet_test_db",
        echo=False,
    )
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(BaseTable().metadata.drop_all)
        await conn.run_sync(BaseTable().metadata.create_all)

    async with async_session() as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_insert_into_outbox(session: AsyncSession):
    payload = {
        "test": "my_data"
    }
    queue = "test-queue"
    
    await insert_into_outbox(
        payload=payload,
        queue=queue,
        session=session,
        commit=True
    )

    result = await session.scalar(select(OutboxTable).order_by(desc(OutboxTable.id)))
    assert isinstance(result, OutboxTable)
    assert result.payload == payload
    assert result.queue == queue


@pytest.mark.asyncio
async def test_get_last_pending_messages_from_outbox(session: AsyncSession):
    payload = {
        "test": "my_test_get_last_pending_messages_from_outboxdata"
    }
    queue = "test-queue"

    await insert_into_outbox(
        payload=payload,
        queue=queue,
        session=session,
        commit=True
    )
    
    result = await get_last_pending_messages_from_outbox(session)
    assert isinstance(result, list)
    assert len(result) >= 1
    assert result[-1].payload == payload
    assert result[-1].queue == queue
    
    await set_status_of_outbox_row(result[-1].id, OutBoxStatuses.FAILED, session)
    await session.refresh(result[-1])
    assert result[-1].status == OutBoxStatuses.FAILED
    
    
@pytest.mark.asyncio
@given(queue_name=st.text(), category=st.text(alphabet=string.ascii_letters, min_size=10))
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
async def test_get_all_categories(
    session: AsyncSession, 
    queue_name: str,
    category: str
):
    with patch("core.database_utils.insert_into_outbox", new_callable=AsyncMock) as mock_outbox:
        # Подготовка тестовых данных
        await session.execute(delete(CategoriesTable))
        await create_row(
            CategoriesTable, 
            {
                "name": category
            },
            session, 
            queue_name
        )
        await session.commit()
        result = await get_all_categories(session, queue_name)
        assert isinstance(result, list)
        assert len(result) >= 1
        assert {"id", "name"} <= set(result[-1].keys())
        assert result[-1]["name"] == category


@pytest.mark.asyncio
async def test_get_all_cards_in_category_with_short_description(session: AsyncSession):
    await create_row(
        CategoriesTable, 
        {
            "id": 1,
            "name": "Интернет и ТВ"
        },
        session, 
        "test_queue"
    )
    
    await session.execute(
        insert(CompaniesTable).values(
            {
                CompaniesTable.id.name: 1,
                CompaniesTable.name.name: "Компания",
                CompaniesTable.short_description.name: "Описание"
            }
        )
    )
    
    test_card = {
        CardsTable.id.name: 1,
        CardsTable.category_id.name: 1,
        CardsTable.company_id.name: 1,
        CardsTable.main_label.name: "Лейбл",
        CardsTable.description_under_label.name: "Описание",
        CardsTable.obtain_method_description.name: "Метод получения"
    }
    await session.execute(insert(CardsTable).values(test_card))
    await session.commit()
    result = await get_all_cards_in_category_with_short_description(1, session, "test_queue")
    
    assert isinstance(result, list)
    assert len(result) > 0
    for key in test_card:
        assert result[-1][key] == test_card[key]


@pytest.mark.asyncio
async def test_get_card_info_by_card_id(session: AsyncSession):
    ...


@pytest.mark.asyncio
async def test_get_all_rows_from_table(session: AsyncSession):
    ...


@pytest.mark.asyncio
async def test_get_full_row_for_admin_by_id(session: AsyncSession):
    ...


@pytest.mark.asyncio
async def test_update_row_by_id(session: AsyncSession):
    ...


@pytest.mark.asyncio
async def test_create_row(session: AsyncSession):
    ...


@pytest.mark.asyncio
async def test_delete_row(session: AsyncSession):
    ...


