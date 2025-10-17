# Changelog

## 17.10.25 14.14
1. Файл core.database_utils.py разделен на файлы dml.py outbox.py specific_select.py и помещены в папку database_utils на место файла database_utils.py
2. Во всех функциях в core.database_utils добавлена обработка спецефичных исключений sqlalchemy/asyncpg таких как IntegrityError SQLAlchemyError OperationalError и др. из модуля sqlalchemy.exc
3. Переписаны тесты под использование session.begin() и добавлен тест на обработку ошибок
