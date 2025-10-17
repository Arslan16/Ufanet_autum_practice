from loguru import logger
from typing import Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select
from sqlalchemy.exc import (
    SQLAlchemyError,
    OperationalError
)

from ..models import (
    CategoriesTable,
    CompaniesTable,
    CardsTable
)
from .outbox import insert_into_outbox


async def get_all_categories(
    session: AsyncSession,
    queue_name: str
) -> list[dict[str, Any]]:
    """
    Извлекает все категории из базы данных и возвращает их в виде списка словарей.

    Функция:
    - Выполняет асинхронный SQL-запрос к таблице категорий;
    - Формирует список словарей, где каждый словарь представляет одну категорию;
    - В случае ошибки логирует её и возвращает пустой список.

    Args:
        session (AsyncSession): Асинхронная сессия SQLAlchemy для работы с базой данных.

    Returns:
        list(dict[str, Any]): Список словарей с ключами (`id`, `name`), значения — данные категорий.
    """
    try:
        async with session.begin():
            stmt: Select = select(CategoriesTable.id, CategoriesTable.name)
            result = await session.execute(stmt)
            await insert_into_outbox(
                payload={
                    "action": "select",
                    "entity": "categories",
                    "fields": ["id", "name"]
                },
                queue=queue_name,
                session=session
            )
            return [dict(res) for res in result.mappings()]
    except OperationalError as exc:
        logger.error(f"Ошибка подключения к БД: {exc}")
        return []

    except SQLAlchemyError as exc:
        logger.error(f"Ошибка SQLAlchemy при выполнении запроса: {exc}")
        return []

    except AttributeError as exc:
        logger.error(f"Неверный объект сессии или таблицы: {exc}")
        return []

    except Exception as exc:
        logger.error(f"Неожиданная ошибка при получении сообщений: {exc}")
        return []


async def get_all_cards_in_category_with_short_description(
    category_id: int,
    session: AsyncSession,
    queue_name: str
) -> list[dict[str, Any]]:
    """
    Извлекает карточки, относящиеся к указанной категории, с данными для отображения в списке.

    Функция:
    - Выполняет асинхронный SQL-запрос к таблице карточек (`CardsTable`);
    - Присоединяет данные о компании из таблицы компаний (`CompaniesTable`);
    - Формирует список словарей с полями карточки и краткой информацией о компании;
    - Логирует ошибки и возвращает пустой список при исключениях.

    Args:
        category_id (int): Идентификатор категории (`categories.id`).
        session (AsyncSession): Асинхронная сессия SQLAlchemy для работы с базой данных.

    Returns:
        list(dict[str, Any]): Список словарей, где каждый словарь содержит:
            - `id`, `main_label`, `description_under_label` карточки;
            - `company_name`, `company_short_description` компании.
    """
    try:
        async with session.begin():
            stmt: Select = select(
                    CardsTable.id,
                    CardsTable.main_label,
                    CardsTable.description_under_label,
                    CompaniesTable.name.label("company_name"),
                    CompaniesTable.short_description.label("company_short_description")
                ).where(CardsTable.category_id == category_id
                ).join(CompaniesTable, CompaniesTable.id == CardsTable.company_id
            )
            result = await session.execute(stmt)
            await insert_into_outbox(
                payload={
                    "action": "select",
                    "entity": "cards",
                    "filters": [
                        {"column": "category_id", "operator": "=", "value": category_id}
                    ],
                    "fields": ["id", "main_label", "description_under_label"],
                    "joined_entities": {
                        "companies": ["name", "short_description"]
                    }
                },
                queue=queue_name,
                session=session
            )
            return [dict(res) for res in result.mappings()]
    except OperationalError as exc:
        logger.error(f"Ошибка подключения к БД: {exc}")
        return []

    except SQLAlchemyError as exc:
        logger.error(f"Ошибка SQLAlchemy при выполнении запроса: {exc}")
        return []

    except AttributeError as exc:
        logger.error(f"Неверный объект сессии или таблицы: {exc}")
        return []

    except Exception as exc:
        logger.error(f"Неожиданная ошибка при получении сообщений: {exc}")
        return []


async def get_card_info_by_card_id(
    card_id: int,
    session: AsyncSession,
    queue_name: str
) -> dict[str, Any]:
    """
    Извлекает полную информацию о карточке по её идентификатору.

    Функция:
    - Выполняет асинхронный SQL-запрос к таблице карточек (`CardsTable`);
    - Извлекает поля, необходимые для отображения в модальном окне;
    - Логирует ошибки и возвращает пустой словарь при исключениях или если карточка не найдена.

    Args:
        card_id (int): Идентификатор карточки (`cards.id`).
        session (AsyncSession): Асинхронная сессия SQLAlchemy для работы с базой данных.

    Returns:
        dict(str, Any): Словарь с полями карточки:
            - `main_label`
            - `description_under_label`
            - `obtain_method_description`
            - `validity_period`
            - `about_partner`
            - `promocode`
            - `call_to_action_link`
            - `call_to_action_btn_label`
        Пустой словарь, если карточка не найдена или произошла ошибка.
    """
    try:
        async with session.begin():
            stmt: Select = select(
                    CardsTable.main_label,
                    CardsTable.description_under_label,
                    CardsTable.obtain_method_description,
                    CardsTable.validity_period,
                    CardsTable.about_partner,
                    CardsTable.promocode,
                    CardsTable.call_to_action_link,
                    CardsTable.call_to_action_btn_label
                ).where(CardsTable.id == card_id
            )
            result = await session.execute(stmt)
            await insert_into_outbox(
                payload={
                    "action": "select",
                    "entity": "cards",
                    "filters": [
                        {"column": "id", "operator": "=", "value": card_id}
                    ],
                    "fields": [
                        "main_label", "description_under_label", "obtain_method_description",
                        "validity_period", "about_partner", "promocode", "call_to_action_link",
                        "call_to_action_btn_label"
                    ]
                },
                queue=queue_name,
                session=session
            )
            return dict(result.mappings().first())
    except OperationalError as exc:
        logger.error(f"Ошибка подключения к БД: {exc}")
        return {}

    except SQLAlchemyError as exc:
        logger.error(f"Ошибка SQLAlchemy при выполнении запроса: {exc}")
        return {}

    except AttributeError as exc:
        logger.error(f"Неверный объект сессии или таблицы: {exc}")
        return {}

    except Exception as exc:
        logger.error(f"Неожиданная ошибка при получении сообщений: {exc}")
        return {}

