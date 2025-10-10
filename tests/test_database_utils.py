import pytest

from unittest.mock import AsyncMock, patch
from hypothesis import given, settings
from hypothesis import strategies as st
from sqlalchemy import delete, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.core_types import OutBoxStatuses
from core.database_utils import (
    create_row,
    delete_row,
    get_all_cards_in_category_with_short_description,
    get_all_categories,
    get_all_rows_from_table,
    get_card_info_by_card_id,
    get_full_row_for_admin_by_id,
    get_last_pending_messages_from_outbox,
    insert_into_outbox,
    set_status_of_outbox_row,
    update_row_by_id,
)

from factories import (
    test_async_session_maker,
    engine,
    card_factory,
    category_factory,
    company_factory,
    my_hypothesis_settings,
    queue_factory
)

from core.models import BaseTable, CardsTable, CategoriesTable, CompaniesTable, OutboxTable


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


@pytest.mark.asyncio
@given(
    queue_name=queue_factory(),
    payload=card_factory()
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
    queue_name=queue_factory(),
    category=category_factory()
)
@settings(**my_hypothesis_settings)
async def test_get_all_categories(
    session: AsyncSession,
    queue_name: str,
    category: dict
):
    with patch("core.database_utils.insert_into_outbox", new_callable=AsyncMock):
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
    card=card_factory(),
    queue_name=queue_factory()
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


@pytest.mark.asyncio
@given(
    card=card_factory(),
    category=category_factory(),
    company=company_factory(),
    queue_name=queue_factory()
)
@settings(**my_hypothesis_settings)
async def test_get_card_info_by_card_id(
    session: AsyncSession,
    card: dict,
    category: dict,
    company: dict,
    queue_name: str
):
    with patch("core.database_utils.insert_into_outbox", new_callable=AsyncMock):
        category_id = await create_row(CategoriesTable, category, session, queue_name)
        company_id = await create_row(CompaniesTable, company, session, queue_name)
        card["category_id"] = category_id
        card["company_id"] = company_id
        card_id = await create_row(CardsTable, card, session, queue_name)
        assert isinstance(card_id, int)
        my_card = await get_card_info_by_card_id(card_id, session, queue_name)
        for key in my_card:
            assert card[key] == my_card[key]


@pytest.mark.asyncio
@given(
    categories=st.lists(category_factory(), min_size=5, max_size=10,  unique_by=lambda x: x["name"]),
    companies=st.lists(company_factory(), min_size=5, max_size=10,  unique_by=lambda x: x["name"]),
    cards=st.lists(card_factory(), min_size=5, max_size=10, unique_by=lambda x: x["main_label"]),
    queue_name=queue_factory()
)
@settings(**my_hypothesis_settings)
async def test_get_all_rows_from_table(
    session: AsyncSession,
    categories: list[dict],
    companies: list[dict],
    cards: list[dict],
    queue_name: str
):
    with patch("core.database_utils.insert_into_outbox", new_callable=AsyncMock):
        names: list = []
        for category in categories:
            category["id"] = await create_row(CategoriesTable, category, session, queue_name)
            names.append(category["name"])

        db_categories = await get_all_rows_from_table(CategoriesTable, session, queue_name)
        db_names = {c["name"] for c in db_categories}
        expected_names = {c["name"] for c in categories}

        assert expected_names <= db_names

        names: list = []
        for company in companies:
            company["id"] = await create_row(CompaniesTable, company, session, queue_name)
            names.append(company["name"])

        db_companies = await get_all_rows_from_table(CompaniesTable, session, queue_name)
        db_names = {c["name"] for c in db_companies}
        expected_names = {c["name"] for c in companies}

        assert expected_names <= db_names

        names: list = []
        for card in cards:
            card["category_id"] = categories[0]["id"]
            card["company_id"] = companies[0]["id"]
            card["id"] = await create_row(CardsTable, card, session, queue_name)
            names.append(card["main_label"])

        db_cards = await get_all_rows_from_table(CardsTable, session, queue_name)
        db_names = {c["main_label"] for c in db_cards}
        expected_names = {c["main_label"] for c in cards}

        assert expected_names <= db_names

@pytest.mark.asyncio
@given(
    category=category_factory(),
    company=company_factory(),
    card=card_factory(),
    queue_name=queue_factory()
)
@settings(**my_hypothesis_settings)
async def test_get_full_row_for_admin_by_id(
    session: AsyncSession,
    category: dict,
    company: dict,
    card: dict,
    queue_name: str
):
    with patch("core.database_utils.insert_into_outbox", new_callable=AsyncMock):
        row_id = await create_row(
            CategoriesTable,
            category,
            session,
            queue_name
        )
        category["id"] = row_id
        selected_category = await get_full_row_for_admin_by_id(
            row_id,
            CategoriesTable,
            session,
            queue_name
        )
        
        assert selected_category == category

        row_id = await create_row(
            CompaniesTable,
            company,
            session,
            queue_name
        )
        company["id"] = row_id
        selected_company = await get_full_row_for_admin_by_id(
            row_id,
            CompaniesTable,
            session,
            queue_name
        )
        
        assert selected_company == company

        card["company_id"] = company["id"]
        card["category_id"] = category["id"]

        row_id = await create_row(
            CardsTable,
            card,
            session,
            queue_name
        )

        card["id"] = row_id
        selected_card = await get_full_row_for_admin_by_id(
            row_id,
            CardsTable,
            session,
            queue_name
        )

        assert selected_card == card


@pytest.mark.asyncio
@given(
    category=category_factory(),
    second_category=category_factory(),
    queue_name=queue_factory()
)
@settings(**my_hypothesis_settings)
async def test_update_row_by_id(
    session: AsyncSession,
    category: dict[str, str | int],
    second_category: dict[str, str | int],
    queue_name: str
):
    with patch("core.database_utils.insert_into_outbox", new_callable=AsyncMock):
        row_id = await create_row(
            CategoriesTable,
            category,
            session,
            queue_name
        )
        
        res = await update_row_by_id(
            row_id,
            CategoriesTable,
            second_category,
            session,
            queue_name
        )
        
        assert res is True

        second_category["id"] = row_id
        selected_category = await get_full_row_for_admin_by_id(
            row_id,
            CategoriesTable,
            session,
            queue_name
        )
        
        assert selected_category == second_category


@pytest.mark.asyncio
@given(
    category=category_factory(),
    queue_name=queue_factory()
)
@settings(**my_hypothesis_settings)
async def test_delete_row(
    session: AsyncSession,
    category: dict[str, str | int],
    queue_name: str
):
    with patch("core.database_utils.insert_into_outbox", new_callable=AsyncMock):
        row_id = await create_row(
            CategoriesTable,
            category,
            session,
            queue_name
        )

        res = await delete_row(
            row_id,
            CategoriesTable,
            session,
            queue_name
        )

        assert isinstance(res, bool)

        selected_category = await get_full_row_for_admin_by_id(
            row_id,
            CategoriesTable,
            session,
            queue_name
        )

        assert selected_category == {}

