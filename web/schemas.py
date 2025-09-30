from pydantic import BaseModel


class CardPydanticModel(BaseModel):
    card_id: int


class GetTableDataModel(BaseModel):
    tablename: str

