import enum
from datetime import datetime

from sqlalchemy import JSON, BigInteger, DateTime, Enum, ForeignKey, String
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from .core_types import OutBoxStatuses


class BaseTable(DeclarativeBase, AsyncAttrs):
    """Базовый класс при наследовании от которого создается таблица в бд"""
    ...


class CompaniesTable(BaseTable):
    "Таблица которая содержит информацию о компании, в которых проходит акции"
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(BigInteger, autoincrement=True, primary_key=True)
    "Уникальный идентификатор PK"

    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    "Наименование компании"

    short_description: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    "Краткое описание компании"

    cards: Mapped["CardsTable"] = relationship(back_populates="company")
    "Карточки компаний из cards"


class CategoriesTable(BaseTable):
    "Таблица отражающие возможные категории карточек"
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(BigInteger, autoincrement=True, primary_key=True)
    "Уникальный идентификатор PK"

    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    "Наименование категории"

    cards: Mapped[list["CardsTable"]] = relationship(back_populates="category")
    "Карточки, находящиеся в категории"


class CardsTable(BaseTable):
    "Таблица, хранящая информацию о карточках с ссылкой на категорию"
    __tablename__ = "cards"

    id: Mapped[int] = mapped_column(BigInteger, autoincrement=True, primary_key=True)
    "Уникальный идентификатор PK"

    category_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("categories.id"))
    "Идентификатор категории в которой находится карточки"

    company_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("companies.id"))
    "Идентификатор компании которой принадлежит карточка"

    main_label: Mapped[str] = mapped_column(String)
    "Текст заголовка на карточке"

    description_under_label: Mapped[str] = mapped_column(String)
    "Описание под заголовком"

    obtain_method_description: Mapped[str] = mapped_column(String, nullable=True)
    "Описание раздела 'Как получить'"

    validity_period: Mapped[str] = mapped_column(String, nullable=True)
    "Описание раздела 'Срок действия'"

    about_partner: Mapped[str] = mapped_column(String, nullable=True)
    "Описание раздела 'О партнере'"

    promocode: Mapped[str] = mapped_column(String, nullable=True)
    "Промокод, если есть"

    call_to_action_link: Mapped[str] = mapped_column(String, nullable=True)
    "По какой ссылке должен перейти (Призыв к действию) если есть"

    call_to_action_btn_label: Mapped[str] = mapped_column(String, nullable=True)
    "Надпись на кнопке с ссылкой если есть"

    category: Mapped["CategoriesTable"] = relationship(back_populates="cards")
    "Категория, в которой находится карточка"

    company: Mapped["CompaniesTable"] = relationship(back_populates="cards")
    "Компания, которой принадлежит карточка"


class OutboxTable(BaseTable):
    __tablename__ = "outbox"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    "Уникальный идентификатор PK"

    payload: Mapped[dict] = mapped_column(JSON)
    "Передаваемые данные в сообщении"

    queue: Mapped[str] = mapped_column(String)
    "Наименование очереди в которую нужно отправить сообщение"

    status: Mapped[enum.Enum] = mapped_column(Enum(OutBoxStatuses))
    "Статус сообщения. Перечисление OutBoxStatuses"

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    "Дата создания записи"


tables: dict[str, BaseTable] = {
    CompaniesTable.__tablename__ : CompaniesTable,
    CategoriesTable.__tablename__: CategoriesTable,
    CardsTable.__tablename__: CardsTable
}
"Словарь, который под именем таблицы __tablename__ содержит ссылку на ее класс"

russian_field_names: dict[str, str] = {
    "id": "ИД",
    "name": "Наименование",
    CompaniesTable.short_description.name: "Описание",
    CardsTable.category_id.name: "ИД Категории",
    CardsTable.company_id.name: "ИД Компании",
    CardsTable.main_label.name: "Заголовок карточки",
    CardsTable.description_under_label.name: "Описание под заголовком",
    CardsTable.obtain_method_description.name: "Метод получения",
    CardsTable.validity_period.name: "Срок действия",
    CardsTable.about_partner.name: "О партнере",
    CardsTable.promocode.name: "Промокод",
    CardsTable.call_to_action_link.name: "Ссылка в кнопке карточки",
    CardsTable.call_to_action_btn_label.name: "Надпись на кнопке в карточке"
}
"Русские названия полей таблиц. Ключ - оригинальное название столбца. Значение - перевод на русский"

reverse_russian_field_names: dict[str, str] = {v : k for k, v in russian_field_names.items()}
"""Обратный словарь для перевода с русского на английский. Ключ - перевод на русский.
Значение - оригинальное название столбца"""
