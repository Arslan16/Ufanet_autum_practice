INSERT INTO categories(name) VALUES 
('Категория 1')

INSERT INTO companies(name, short_description) VALUES
('Компания 1', 'Описание компании 1');

INSERT INTO cards(company_id, category_id, main_label, description_under_label, obtain_method_description, validity_period, about_partner) VALUES 
(1, 1, 'Карточка 1', 'Описание 1', 'Описание метода получения 1', 'Описание срока действия 1', 'Текст о партнере 1'), 
(1, 1, 'Карточка 2', 'Описание 2', 'Описание метода получения 2', 'Описание срока действия 2', 'Текст о партнере 2');