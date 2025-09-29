from pydantic import BaseModel


class CardsPydanticModel(BaseModel):
    "Модель для обработки /partnerprogram/cards (Вывести список карточек в категории)"
    category_id: int

