from dataclasses import dataclass
from enum import Enum


@dataclass
class RabbitMQCredentials:
    """
    Параметры подключеня к RabbitMQ:
    
    Args:
        host (str): Хост на котором запущено rmq (Например `127.0.0.1`)
        port (int): Порт на котором хостится rmq (Например `5672`)
        login (str): Логин пользователя (Например `guest`)
        password (str): Пароль пользователя (Например `guest`)
    """
    host: str
    port: int
    login: str
    password: str

    def to_connection_params(self) -> dict:
        return {
            "host": self.host,
            "port": self.port,
            "login": self.login,
            "password": self.password,
        }

    def to_url(self) -> str:
        return f"amqp://{self.login}:{self.password}@{self.host}:{self.port}"


class OutBoxStatuses(Enum):
    PENDING = "pending"        # Ожидает отправки
    SENT = "sent"              # Успешно отправлено
    FAILED = "failed"          # Ошибка отправки
    ARCHIVED = "archived"      # Удалено из активной таблицы

