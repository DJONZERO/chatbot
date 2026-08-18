# Telegram Bot для API hh.ru

Бот-помощник для работы с API hh.ru. Использует RAG (Retrieval-Augmented Generation) с векторным поиском через pgvector и OpenAPI-спецификацию hh.ru.

## Возможности

- 🔍 Поиск информации в официальной документации hh.ru
- 📚 Векторный поиск через pgvector (косинусное расстояние)
- 🤖 Ответы на вопросы об API hh.ru
- 📖 Ссылки на источники в каждом ответе
- ✅ Честные ответы при отсутствии информации

## Технологии

- Python 3.11
- PostgreSQL + pgvector
- SQLAlchemy
- Telegram Bot API
- Sentence Transformers (all-MiniLM-L6-v2)
- Yandex GPT (опционально)

## Установка и запуск

### 1. Клонирование репозитория

```bash
git clone <repository-url>
cd MAX

2. Установка зависимостей

pip install -r requirements.txt

3. Настройка окружения
Скопируйте .env.example в .env и заполните:


cp .env.example .env
Настройки:

TELEGRAM_BOT_TOKEN — токен бота от @BotFather

DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD — для PostgreSQL

SIMILARITY_THRESHOLD — порог релевантности (рекомендуется 0.3)

MAX_RAG_FRAGMENTS — количество фрагментов для ответа (5)

4. Запуск PostgreSQL с pgvector через Docker

docker run -d --name postgres-pgvector -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=chatbot_db -p 5432:5432 pgvector/pgvector:pg18
5. Инициализация базы данных

python -m app.init_db
6. Запуск бота

python -m app.main
Команды бота
/start — Приветствие

/help — Помощь

/history — История сообщений

/knowledge <запрос> — Поиск в базе знаний

/stats — Статистика базы знаний

Структура проекта

MAX/
├── app/
│   ├── __init__.py
│   ├── main.py              # Точка входа
│   ├── database.py          # Подключение к БД
│   ├── models.py            # Модели SQLAlchemy
│   ├── doc_loader.py        # Загрузка OpenAPI
│   ├── retriever.py         # Поиск (векторный + текстовый)
│   ├── yandex_assistant.py  # Генерация ответов
│   ├── telegram_bot.py      # Telegram бот
│   └── init_db.py           # Инициализация БД
├── .env
├── .env.example
├── requirements.txt
└── README.md