from typing import Any

from pydantic import BaseModel


class CardPydanticModel(BaseModel):
    """
    Модель данных для запроса информации о конкретной карточке.

    Attributes:
        card_id (int): Идентификатор карточки (cards.id) для извлечения полной информации.
    """
    card_id: int


class GetTableDataModel(BaseModel):
    """
    Модель данных для запроса всех строк таблицы.

    Attributes:
        tablename (str): Имя таблицы в базе данных для получения всех записей.
    """
    tablename: str


class GetTableRowModel(BaseModel):
    """
    Модель данных для запроса одной конкретной строки таблицы по id.

    Attributes:
        tablename (str): Имя таблицы, в которой находится запись.
        id (int): Идентификатор записи (row_id) в таблице.
    """
    tablename: str
    id: int


class SaveRowModel(BaseModel):
    """
    Модель данных для обновления существующей записи таблицы.

    Attributes:
        tablename (str): Имя таблицы, в которой обновляется запись.
        id (int): Идентификатор обновляемой записи.
        data (dict ([str, Any])): Словарь с данными для обновления, где ключ = имя столбца, значение = новое значение.
    """
    tablename: str
    id: int
    data: dict[str, Any]


class CreateRowGetModalModel(BaseModel):
    """
    Модель данных для запроса HTML модального окна создания новой записи.

    Attributes:
        tablename (str): Имя таблицы, для которой необходимо отобразить модальное окно создания записи.
    """
    tablename: str


class CreateRowModel(BaseModel):
    """
    Модель данных для создания новой записи в таблице.

    Attributes:
        tablename (str): Имя таблицы, в которую создается запись.
        data (dict ([str, Any])): Словарь с данными для новой записи, где ключ = имя столбца, значение = значение.
    """
    tablename: str
    data: dict[str, Any]


class DeleteRowModel(BaseModel):
    """
    Модель данных для удаления существующей записи из таблицы.

    Attributes:
        tablename (str): Имя таблицы, из которой удаляется запись.
        id (int): Идентификатор записи, подлежащей удалению.
    """
    tablename: str
    id: int
