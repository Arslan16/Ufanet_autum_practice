import asyncpg

from loguru import logger
from typing import Any
from sqlalchemy import insert, select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Insert, Select, Update, Delete
from sqlalchemy.exc import (
    SQLAlchemyError,
    OperationalError,
    IntegrityError,
    DBAPIError
)

from ..models import BaseTable
from .outbox import insert_into_outbox


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
        async with session.begin():
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
        async with session.begin():
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
        async with session.begin():
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
                session=session
            )
            await session.commit()
            return True
    except IntegrityError as exc:
        await session.rollback()
        logger.error(f"Нарушение целостности данных при обновлении {row_id}: {exc}")
        return str(exc)

    except OperationalError as exc:
        await session.rollback()
        logger.error(f"Ошибка подключения к БД при обновлении {row_id}: {exc}")
        return str(exc)

    except SQLAlchemyError as exc:
        await session.rollback()
        logger.error(f"Ошибка SQLAlchemy при обновлении {row_id}: {exc}")
        return str(exc)

    except Exception as exc:
        await session.rollback()
        logger.error(f"Неожиданная ошибка при обновлении {row_id}: {exc}")
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
        async with session.begin():
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
                session=session
            )
            await session.commit()
            return res
    except (IntegrityError, asyncpg.exceptions.UniqueViolationError) as exc:
        logger.warning(f"Нарушение целостности данных: {exc}")
        return False

    except (OperationalError, DBAPIError) as exc:
        logger.error(f"Ошибка базы данных: {exc}")
        return False

    except SQLAlchemyError as exc:
        logger.error(f"Ошибка SQLAlchemy: {exc}")
        return False

    except TypeError as exc:
        logger.error(f"Неверный тип данных: {exc}")
        return False

    except Exception as exc:
        logger.error(f"Неожиданная ошибка: {exc}")
        return False


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
        async with session.begin():
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
                session=session
            )
            await session.commit()
            return True
    except (IntegrityError, asyncpg.exceptions.UniqueViolationError) as exc:
        logger.error(f"Нарушение целостности данных: {exc}")
        return str(exc)

    except (OperationalError, DBAPIError) as exc:
        logger.error(f"Ошибка базы данных: {exc}")
        return str(exc)

    except SQLAlchemyError as exc:
        logger.error(f"Ошибка SQLAlchemy: {exc}")
        return str(exc)

    except TypeError as exc:
        logger.error(f"Неверный тип данных: {exc}")
        return str(exc)

    except Exception as exc:
        logger.error(f"Неожиданная ошибка: {exc}")
        return str(exc)
