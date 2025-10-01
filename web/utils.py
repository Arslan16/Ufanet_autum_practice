from typing import Any
from loguru import logger
from sqlalchemy import String, BigInteger

from core.models import BaseTable, reverse_russian_field_names


def map_columns_to_table_types(table: BaseTable, data: dict[str, str]) -> dict[str, Any]:
    "Валидация и приведение к соответсвующим типам столбца таблицы"
    try: 
        clear_result: dict = dict()
        data = { reverse_russian_field_names.get(key, key) : data[key] for key in data.keys()}
        "Словарь отражающий запись в таблице, но уже с оригинальным названием столбца на английском"

        for column in table.__table__.columns:
            if data.get(column.name):
                if data[column.name] in ("", None):
                    clear_result[column.name] = None
                elif isinstance(column.type, String):
                    clear_result[column.name] = str(data[column.name])
                elif isinstance(column.type, BigInteger):
                    clear_result[column.name] = int(data[column.name])
                else:
                    clear_result[column.name] = data[column.name]
                # можно добавить и остальные проверки на тип столбца и соответственное приведение к типу
                # Используются только BigInteger и String т.к. только они представлены в текущих таблицах бд
        return clear_result
    except Exception as exc:
        logger.error(exc)
