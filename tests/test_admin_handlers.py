import pytest

from httpx import ASGITransport, AsyncClient
from hypothesis import given, settings
from hypothesis import strategies as st
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from factories import category_factory, my_hypothesis_settings, queue_factory
from core.database_utils import create_row, get_full_row_for_admin_by_id
from core.models import CategoriesTable
from tests.test_database_utils import session
from web.dependencies import async_session_generator
from web_main import app as fastapi_app


async def get_session():
    return session


@pytest.fixture(scope="function")
async def ac(session: AsyncSession):
    fastapi_app.dependency_overrides[async_session_generator] = lambda: session
    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(transport=transport, base_url="http://localhost:8000/Ufanet_autum_practice/admin") as ac:
        yield ac

    fastapi_app.dependency_overrides.pop(async_session_generator, None)


@pytest.mark.asyncio
async def test_index_get_handler(
    ac: AsyncClient
):
    response = await ac.get("/")

    successful_code = 200
    assert response.status_code == successful_code
    text = response.text

    assert "<html" in text.lower() or "<!doctype" in text.lower()

    assert "Комании" in text
    assert "Карточки" in text
    assert "Категории" in text

    assert "companies" in text
    assert "cards" in text
    assert "categories" in text


@pytest.mark.asyncio
@given(
    categories=st.lists(category_factory(), min_size=5, max_size=10,  unique_by=lambda x: x["name"]),
    queue_name=queue_factory()
)
@settings(**my_hypothesis_settings)
async def test_get_table_data(
    ac: AsyncClient,
    session: AsyncSession,
    categories: list[dict],
    queue_name: str
):
    await session.execute(delete(CategoriesTable))
    await session.commit()
    for category in categories:
        await create_row(CategoriesTable, category, session, queue_name)

    test_tablename = CategoriesTable.__tablename__

    response = await ac.post(
        "/get_table_data",
        json={
            "tablename": test_tablename
        }
    )

    successful_code = 200
    assert response.status_code == successful_code
    text = response.text

    assert "<table" in text.lower()

    for category in categories:
        for value in category.values():
            assert str(value) in text.strip(" \n")


@pytest.mark.asyncio
@given(
    categories=st.lists(category_factory(), min_size=2, max_size=3,  unique_by=lambda x: x["name"]),
    queue_name=queue_factory()
)
@settings(**my_hypothesis_settings)
async def test_get_table_data_post_handler(
    ac: AsyncClient,
    session: AsyncSession,
    categories: list[dict],
    queue_name: str
):
    for category in categories:
        row_id = await create_row(
            CategoriesTable,
            category,
            session,
            queue_name
        )
        category["id"] = row_id

    response = await ac.post(
        "/get_table_data",
        json={"tablename": CategoriesTable.__tablename__}
    )

    successful_code = 200
    assert response.status_code == successful_code
    text = response.text

    assert "<table" in text.lower()

    for row in categories:
        for value in row.values():
            assert str(value) in text.strip(" \n")


@pytest.mark.asyncio
@given(
    category=category_factory(),
    queue_name=queue_factory()
)
@settings(**my_hypothesis_settings)
async def test_get_table_row_post_handler(
    ac: AsyncClient,
    session: AsyncSession,
    category: dict,
    queue_name: str
):
    await session.execute(delete(CategoriesTable))
    row_id = await create_row(
        CategoriesTable,
        category,
        session,
        queue_name
    )
    response = await ac.post(
        "/get_table_row",
        json={
            "tablename": CategoriesTable.__tablename__,
            "id": row_id
        }
    )

    successful_code = 200
    assert response.status_code == successful_code
    text = response.text

    for value in category.values():
        assert str(value) in text.strip(" \n")


@pytest.mark.asyncio
@given(
    category=category_factory(),
    new_category=category_factory(),
    queue_name=queue_factory()
)
@settings(**my_hypothesis_settings)
async def test_save_row_post_hanlder(
    ac: AsyncClient,
    session: AsyncSession,
    category: dict[str, str | int],
    new_category: dict[str, str | int],
    queue_name: str
):

    row_id = await create_row(
        CategoriesTable,
        category,
        session,
        queue_name
    )

    response = await ac.post(
        "/save_row",
        json={
            "tablename": CategoriesTable.__tablename__,
            "id": row_id,
            "data": new_category
        }
    )

    successful_code: int = 200
    assert response.status_code == successful_code

    new_category["id"] = row_id
    updated_row = await get_full_row_for_admin_by_id(
        row_id,
        CategoriesTable,
        session,
        queue_name
    )

    assert updated_row == new_category


