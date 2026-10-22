# Clinic Bot

Telegram-бот для записи к врачу в медицинской клинике.

## Возможности
- Запись к врачу: выбор специалиста и свободного времени
- Просмотр своих записей
- Защита от двойного бронирования слота

## Стек
- Python 3.10+
- aiogram 3
- PostgreSQL + SQLAlchemy 2
- python-dotenv

## Структура
- bot.py — хэндлеры и запуск бота
- db.py — модели и функции работы с БД
- config.py — чтение переменных окружения

## Запуск
1. pip install -r requirements.txt
2. Создать .env по образцу .env.example
3. python -c "from db import init_db; init_db()"
4. python bot.py

## Примечание
Для работы требуется доступ к api.telegram.org — нужен VPN или прокси.
