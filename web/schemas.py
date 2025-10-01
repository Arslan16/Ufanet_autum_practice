from typing import Any
from pydantic import BaseModel


class CardPydanticModel(BaseModel):
    card_id: int


class GetTableDataModel(BaseModel):
    tablename: str


class GetTableRowModel(BaseModel):
    tablename: str
    id: int


class SaveRowModel(BaseModel):
    tablename: str
    id: int
    data: dict[str, Any]
