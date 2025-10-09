import pytest
from unittest.mock import AsyncMock, patch
from hypothesis import given, settings
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

from factories import (
    my_hypothesis_settings,
    card_factory,
    category_factory,
    company_factory,
    queue_factory
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


@pytest.fixture(autouse=True)
async def clear_db(session):
    for table in reversed(BaseTable.metadata.sorted_tables):
        await session.execute(table.delete())
    await session.commit()


@pytest.fixture(autouse=True)
async def cleanup_session(session: AsyncSession):
    yield
    await session.rollback()


@pytest.mark.asyncio
@given(
    queue_name=queue_factory,
    payload=card_factory
)
@settings(**my_hypothesis_settings)
async def test_insert_into_outbox(
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

    result = await session.scalar(select(OutboxTable).order_by(desc(OutboxTable.id)))
    assert isinstance(result, OutboxTable)
    assert result.payload == payload
    assert result.queue == queue_name


@pytest.mark.asyncio
@given(
    queue_name=queue_factory, 
    payload=card_factory
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
        session=session,
        commit=True
    )
    
    result = await get_last_pending_messages_from_outbox(session)
    assert isinstance(result, list)
    assert len(result) >= 1
    assert result[-1].payload == payload
    assert result[-1].queue == queue_name
    
    await set_status_of_outbox_row(result[-1].id, OutBoxStatuses.FAILED, session)
    await session.refresh(result[-1])
    assert result[-1].status == OutBoxStatuses.FAILED
    
    
@pytest.mark.asyncio
@given(
    queue_name=queue_factory, 
    category=category_factory()
)
@settings(**my_hypothesis_settings)
async def test_get_all_categories(
    session: AsyncSession, 
    queue_name: str,
    category: dict
):
    with patch("core.database_utils.insert_into_outbox", new_callable=AsyncMock):
        # Подготовка тестовых данных
        await session.execute(delete(CategoriesTable))
        await create_row(
            CategoriesTable,
            category,
            session, 
            queue_name
        )
        await session.commit()
        result = await get_all_categories(session, queue_name)
        assert isinstance(result, list)
        assert len(result) >= 1
        assert {"id", "name"} <= set(result[-1].keys())
        assert result[-1]["name"] == category["name"]


@pytest.mark.asyncio
@given(
    category=category_factory(),
    company=company_factory(),
    card=card_factory,
    queue_name=queue_factory,
)
@settings(**my_hypothesis_settings)
async def test_get_all_cards_in_category_with_short_description(
    session: AsyncSession,
    category: dict,
    company: dict,
    card: dict,
    queue_name: str
):
    with patch("core.database_utils.insert_into_outbox", new_callable=AsyncMock):
        # создание записей
        category_id = await create_row(CategoriesTable, category, session, queue_name)
        company_id = await create_row(CompaniesTable, company, session, queue_name)
        card["category_id"] = category_id
        card["company_id"] = company_id
        await create_row(CardsTable, card, session, queue_name)

        result = await get_all_cards_in_category_with_short_description(category_id, session, queue_name)

        assert isinstance(result, list)
        assert len(result) > 0
        assert result[-1]["main_label"] == card["main_label"]


# @pytest.mark.asyncio
# async def test_get_card_info_by_card_id(session: AsyncSession):
#     ...


# @pytest.mark.asyncio
# async def test_get_all_rows_from_table(session: AsyncSession):
#     ...


# @pytest.mark.asyncio
# async def test_get_full_row_for_admin_by_id(session: AsyncSession):
#     ...


# @pytest.mark.asyncio
# async def test_update_row_by_id(session: AsyncSession):
#     ...


# @pytest.mark.asyncio
# async def test_create_row(session: AsyncSession):
#     ...


# @pytest.mark.asyncio
# async def test_delete_row(session: AsyncSession):
#     ...


