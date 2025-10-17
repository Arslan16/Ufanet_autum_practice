import asyncpg

from datetime import datetime

from loguru import logger
from sqlalchemy import insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Insert, Select, Update
from sqlalchemy.exc import (
    SQLAlchemyError,
    IntegrityError,
    OperationalError,
    DBAPIError
)

from ..core_types import OutBoxStatuses
from ..models import OutboxTable


async def insert_into_outbox(
    payload: dict,
    queue: str,
    session: AsyncSession,
    status: OutBoxStatuses = OutBoxStatuses.PENDING
) -> bool:
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
        logger.debug("Запись в outbox успешна!")
        return True
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
    except IntegrityError as exc:
        await session.rollback()
        logger.error(f"Нарушение целостности данных при обновлении {row_id}: {exc}")
        return False

    except OperationalError as exc:
        await session.rollback()
        logger.error(f"Ошибка подключения к БД при обновлении {row_id}: {exc}")
        return False

    except SQLAlchemyError as exc:
        await session.rollback()
        logger.error(f"Ошибка SQLAlchemy при обновлении {row_id}: {exc}")
        return False

    except Exception as exc:
        await session.rollback()
        logger.error(f"Неожиданная ошибка при обновлении {row_id}: {exc}")
        return False

