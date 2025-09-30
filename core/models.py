from sqlalchemy import BigInteger, String, ForeignKey
from sqlalchemy.orm import mapped_column, DeclarativeBase, relationship, Mapped
from sqlalchemy.ext.asyncio import AsyncAttrs


class BaseTable(DeclarativeBase, AsyncAttrs):
    """Базовый класс при наследовании от которого создается таблица в бд"""
    ...


class CompaniesTable(BaseTable):
    "Таблица которая содержит информацию о компании, в которых проходит акции"
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(BigInteger, autoincrement=True, primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False) # Имя раздела
    short_description: Mapped[str] = mapped_column(String, unique=True, nullable=False) # Имя раздела
    
    cards: Mapped["CardsTable"] = relationship(back_populates="company")


class CategoriesTable(BaseTable):
    "Таблица отражающие возможные категории карточек"
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(BigInteger, autoincrement=True, primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False) # Имя раздела

    cards: Mapped[list["CardsTable"]] = relationship(back_populates="category")


class CardsTable(BaseTable):
    "Таблица, хранящая информацию о карточках с ссылкой на категорию"
    __tablename__ = "cards"

    id: Mapped[int] = mapped_column(BigInteger, autoincrement=True, primary_key=True)
    category_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("categories.id"))
    company_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("companies.id"))
    main_label: Mapped[str] = mapped_column(String) # Заголовок на карточке
    description_under_label: Mapped[str] = mapped_column(String) # Описание под заголовком
    obtain_method_description: Mapped[str] = mapped_column(String, nullable=True) # Описание раздела "Как получить"
    validity_period: Mapped[str] = mapped_column(String, nullable=True) # Описание раздела "Срок действия"
    about_partner: Mapped[str] = mapped_column(String, nullable=True) # Описание раздела "О партнере"
    promocode: Mapped[str] = mapped_column(String, nullable=True) # Промокод, если есть
    call_to_action_link: Mapped[str] = mapped_column(String, nullable=True) # По какой ссылке должен перейти (Призыв к действию) если есть
    call_to_action_btn_label: Mapped[str] = mapped_column(String, nullable=True) # Надпись на кнопке с ссылкой если есть

    category: Mapped["CategoriesTable"] = relationship(back_populates="cards")
    company: Mapped["CompaniesTable"] = relationship(back_populates="cards")


dict_tables: dict[str, BaseTable] = {
    CompaniesTable.__tablename__ : CompaniesTable,
    CategoriesTable.__tablename__: CategoriesTable,
    CardsTable.__tablename__: CardsTable
}
"Словарь, который под именем таблицы __tablename__ содержит ссылку на ее класс"
