INSERT INTO categories(name) VALUES 
('Категория 1'), ('Категория 2');

INSERT INTO companies(name, short_description) VALUES
('Компания 1', 'Описание компании 1');

INSERT INTO cards(company_id, category_id, main_label, description_under_label) VALUES 
(1, 1, 'Карточка 1', 'Описание 1'), (1, 1, 'Карточка 2', 'Описание 2');