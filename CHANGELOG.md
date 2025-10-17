# Changelog

## 17.10.25 14.14
1. Файл core.database_utils.py разделен на файлы dml.py outbox.py specific_select.py и помещены в папку database_utils на место файла database_utils.py
2. Во всех функциях в core.database_utils добавлена обработка спецефичных исключений sqlalchemy/asyncpg таких как IntegrityError SQLAlchemyError OperationalError и др. из модуля sqlalchemy.exc
3. Переписаны тесты под использование session.begin() и добавлен тест на обработку ошибок

## 17.10.25 15.42
1. Создан класс RabbitMQManager, который объеденил в себе регистрацию callback на очередь и отправку сообщения в очередь, также как создание, закрытие соединения
2. Переписан bot_main.py под использование RabbitMQManager и callback
3. Переписан outbox_main.py под использование RabbitMQManager
4. Переписаны тесты bot_main и outbox_main под использование RabbitMQManager
