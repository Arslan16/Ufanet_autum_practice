from sqlalchemy import BigInteger, String, ForeignKey
from sqlalchemy.orm import mapped_column, DeclarativeBase, Mapped
from sqlalchemy.ext.asyncio import AsyncAttrs


class BaseTable(DeclarativeBase, AsyncAttrs):
    """Базовый класс при наследовании от которого создается таблица в бд"""
    ...


class CategoriesTable(BaseTable):
    "Таблица отражающие возможные категории карточек"
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(BigInteger, autoincrement=True, primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False) # Имя раздела


class CardsTable(BaseTable):
    "Таблица, хранящая информацию о карточках с ссылкой на категорию"
    __tablename__ = "cards"

    id: Mapped[int] = mapped_column(BigInteger, autoincrement=True, primary_key=True)
    category_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("categories.id"))
    obtain_method_description: Mapped[str] = mapped_column(String) # Описание раздела "Как получить"
    validity_period: Mapped[str] = mapped_column(String) # Описание раздела "Срок действия"
    about_partner: Mapped[str] = mapped_column(String) # Описание раздела "О партнере"
    promocode: Mapped[str] = mapped_column(String) # Промокод, если есть
    call_to_action_link: Mapped[str] = mapped_column(String) # По какой ссылке должен перейти (Призыв к действию) если есть
    call_to_action_btn_label: Mapped[str] = mapped_column(String) # Надпись на кнопке с ссылкой если есть
