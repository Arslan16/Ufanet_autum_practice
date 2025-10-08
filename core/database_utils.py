from datetime import datetime
from typing import Any

from loguru import logger
from sqlalchemy import delete, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Delete, Insert, Select, Update

from .core_types import OutBoxStatuses
from .models import BaseTable, CardsTable, CategoriesTable, CompaniesTable, OutboxTable


async def insert_into_outbox(
    payload: dict,
    queue: str,
    session: AsyncSession,
    status: OutBoxStatuses = OutBoxStatuses.PENDING,
    commit: bool = True
):
    """
    Добавляет запись в outbox с данными payload
    Args:
        payload (dict): передаваемые данные между сервисами
        queue (str): Имя очереди в которое будет отправлено сообщение
        session (AsyncSession): Асинхронная сессия SQLAlchemy для работы с базой данных
        status (OutboxStatuses): статус сообщения, по умолчанияю `PENDING`
    """
    try:
        payload["executed_at"] = datetime.now().isoformat()
        stmt: Insert = insert(OutboxTable).values(payload=payload, queue=queue, status=status)
        await session.execute(stmt)
        if commit:
            await session.commit()
        logger.debug("Запись в outbox успешна!")
    except Exception as exc:
        logger.error(exc)


async def get_last_pending_messages_from_outbox(
    session: AsyncSession
) -> list[OutboxTable]:
    """
    Извлекает из `outbox` все сообщения из тех что ожидают отправки в брокер от саммого позднего до раннего
    Args:
        session (AsyncSession): Асинхронная сессия SQLAlchemy для работы с базой данных

    Returns:
        (list[OutboxTable]): Список записей из outbox.
    """
    try:
        stmt: Select = select(OutboxTable
                       ).where(OutboxTable.status == OutBoxStatuses.PENDING
                       ).order_by(OutboxTable.created_at)
        result = await session.scalars(stmt)
        return list(result)
    except Exception as exc:
        logger.error(exc)
        return []


async def set_status_of_outbox_row(
    row_id: int,
    status: OutBoxStatuses,
    session: AsyncSession
) -> bool:
    """
    Присваивает записи из `outbox` новый статус
    Args:
        row_id (int): Идентификатор записи
        status (OutboxStatuses): Значение из перечисления `OutboxStatuses`
        session (AsyncSession): Асинхронная сессия SQLAlchemy для работы с базой данных

    Returns:
        bool: `True` если ошибок при обновлении не возникло, иначе `False`.
    """
    try:
        stmt: Update = update(OutboxTable
                       ).values(status=status
                       ).where(OutboxTable.id == row_id
        )
        await session.execute(stmt)
        await session.commit()
        return True
    except Exception as exc:
        logger.error(exc)
        return False


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
    except Exception as exc:
        logger.error(exc)
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
    except Exception as exc:
        logger.error(exc)
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
    except Exception as exc:
        logger.error(exc)
        return {}


async def get_all_rows_from_table(
    table: BaseTable,
    session: AsyncSession,
    queue_name: str
) -> list[dict[str, Any]]:
    """
    Извлекает все строки из указанной таблицы базы данных.

    Функция:
    - Определяет все столбцы таблицы через её модель (`table.__table__.columns`);
    - Выполняет асинхронный запрос к базе данных для получения всех записей;
    - Логирует ошибки и возвращает пустой список при исключениях.

    Args:
        table (BaseTable): Модель SQLAlchemy, представляющая таблицу базы данных.
        session (AsyncSession): Асинхронная сессия SQLAlchemy для работы с базой данных.

    Returns:
        list(dict[str, Any]): Список словарей, где ключ = имя столбца, значение = значение столбца.
        Пустой список, если таблица пуста или произошла ошибка.
    """
    try:
        stmt: Select = select(*table.__table__.columns)
        result = await session.execute(stmt)
        await insert_into_outbox(
            payload={
                "action": "select",
                "entity": table.__tablename__,
                "fields": [column.name for column in table.__table__.columns]
            },
            queue=queue_name,
            session=session
        )
        return [dict(res) for res in result.mappings().all()]
    except Exception as exc:
        logger.error(exc)
        return []


async def get_full_row_for_admin_by_id(
    row_id: int,
    table: BaseTable,
    session: AsyncSession,
    queue_name: str
) -> dict[str, str | int]:
    """
    Извлекает полную информацию о конкретной записи из таблицы по её ID для редактирования в админ-панели.

    Функция:
    - Определяет все столбцы таблицы через её модель (`table.__table__.columns`);
    - Выполняет асинхронный запрос к базе данных для получения записи с указанным `row_id`;
    - Возвращает словарь с ключами = именам столбцов и значениями = содержимому ячеек;
    - Логирует ошибки и возвращает пустой словарь при исключениях или если запись не найдена.

    Args:
        row_id (int): Идентификатор записи в таблице.
        table (BaseTable): Модель SQLAlchemy, представляющая таблицу базы данных.
        session (AsyncSession): Асинхронная сессия SQLAlchemy для работы с базой данных.

    Returns:
        dict ([str, str | int]): Словарь с полной информацией о записи.
        Пустой словарь, если запись не найдена или произошла ошибка.
    """
    try:
        stmt: Select = select(
                *table.__table__.columns
            ).where(table.id == row_id
        )
        result = await session.execute(stmt)
        await insert_into_outbox(
            payload={
                "action": "select",
                "entity": table.__tablename__,
                "fields": [column.name for column in table.__table__.columns],
                "filters": [
                    {"column": "id", "operator": "=", "value": row_id}
                ]
            },
            queue=queue_name,
            session=session
        )
        return dict(result.mappings().first())
    except Exception as exc:
        logger.error(exc)
        return {}


async def update_row_by_id(
    row_id: int,
    table: BaseTable,
    data: dict[str, str | int],
    session: AsyncSession,
    queue_name: str
) -> bool | str:
    """
    Обновляет запись в таблице по её ID с переданными данными.

    Функция:
    - Формирует асинхронный SQL-запрос на обновление значений столбцов;
    - Выполняет обновление записи с указанным `row_id`;
    - Коммитит изменения в базу данных;
    - Логирует ошибки и возвращает текст ошибки при неудаче.

    Args:
        row_id (int): Идентификатор обновляемой записи.
        table (BaseTable): Модель SQLAlchemy, представляющая таблицу базы данных.
        data (dict ([str, str | int])): Словарь с данными для обновления. Ключ = имя столбца, значение = новое значение.
        session (AsyncSession): Асинхронная сессия SQLAlchemy для работы с БД.

    Returns:
        bool | str: True, если обновление прошло успешно; иначе строка с текстом ошибки.
    """
    try:
        stmt: Update = update(table).values(**data).where(table.id == row_id)
        await session.execute(stmt)
        await insert_into_outbox(
            payload={
                "action": "update",
                "entity": table.__tablename__,
                "fields": dict(**data),
                "filters": [
                    {"column": "id", "operator": "=", "value": row_id}
                ]
            },
            queue=queue_name,
            session=session,
            commit=False
        )
        await session.commit()
        return True
    except Exception as exc:
        logger.error(exc)
        return str(exc)


async def create_row(
    table: BaseTable,
    data: dict[str, Any],
    session: AsyncSession,
    queue_name: str
) -> int | str:
    """
    Создает новую запись в указанной таблице с переданными данными.

    Функция:
    - Формирует объект таблицы с переданными значениями столбцов;
    - Добавляет объект в сессию и коммитит изменения в базу данных;
    - Обновляет объект, чтобы получить его ID после вставки;
    - Логирует ошибки и возвращает текст ошибки при неудаче.

    Args:
        table (BaseTable): Модель SQLAlchemy, представляющая таблицу базы данных.
        data (dict ([str, Any])): Словарь с данными для новой записи. Ключ = имя столбца, значение = значение.
        session (AsyncSession): Асинхронная сессия SQLAlchemy для работы с БД.

    Returns:
        int | str: ID созданной записи, если вставка успешна; иначе строка с текстом ошибки.
    """
    try:
        stmt: Insert = insert(table).values(**data).returning(table.id)
        res: int = await session.scalar(stmt)
        data["id"] = res
        await insert_into_outbox(
            payload={
                "action": "insert",
                "entity": table.__tablename__,
                "fields": dict(**data)
            },
            queue=queue_name,
            session=session,
            commit=False
        )
        await session.commit()
        return res
    except Exception as exc:
        logger.error(exc)
        return str(exc)


async def delete_row(
    row_id: int,
    table: BaseTable,
    session: AsyncSession,
    queue_name: str
) -> bool | str:
    """
    Удаляет запись из указанной таблицы по её ID.

    Функция:
    - Формирует запрос на удаление записи с заданным row_id;
    - Выполняет запрос и коммитит изменения в базу данных;
    - Логирует ошибки и возвращает текст ошибки при неудаче.

    Args:
        row_id (int): ID записи, которую нужно удалить.
        table (BaseTable): Модель SQLAlchemy, представляющая таблицу базы данных.
        session (AsyncSession): Асинхронная сессия SQLAlchemy для работы с БД.

    Returns:
        bool | str: True при успешном удалении; иначе строка с текстом ошибки.
    """
    try:
        stmt: Delete = delete(table).where(table.id == row_id)
        await session.execute(stmt)
        await insert_into_outbox(
            payload={
                "action": "delete",
                "entity": table.__tablename__,
                "filters": [
                    {"column": "id", "operator": "=", "value": row_id}
                ]
            },
            queue=queue_name,
            session=session,
            commit=False
        )
        await session.commit()
        return True
    except Exception as exc:
        logger.error(exc)
        return str(exc)
