<<<<<<< HEAD
🤖 Чат-бот с интеграцией MAX, Yandex GPT и Telegram

## 📖 Описание
Чат-бот на основе **Yandex GPT** с интеграцией **MAX** и **Telegram**. Бот обрабатывает сообщения, сохраняет историю диалогов в **PostgreSQL** и отвечает на вопросы с использованием AI.

### 🧩 Модули проекта
- **Telegram** — получение и отправка сообщений
- **Yandex GPT** — генерация ответов (или режим заглушки)
=======
# 🤖 Чат-бот — помощник по API hh.ru

## Описание
Чат-бот на основе **Yandex GPT** с интеграцией **Telegram** и **PostgreSQL**. Бот помогает пользователям разбираться с API hh.ru — отвечает на вопросы, даёт инструкции, подсказывает параметры запросов.

### 🧩 Модули проекта
- **Telegram** — получение и отправка сообщений
- **Yandex GPT** — генерация ответов 
>>>>>>> b99ea6d (Добавлен .env.example без секретов)
- **MAX** — интеграция с платформой MAX (заглушка)
- **База данных (PostgreSQL)** — хранение пользователей, истории, базы знаний и логов
- **Общий модуль** — координация всех модулей

---

## 🚀 Запуск проекта

Команда	Описание
/start	Приветственное сообщение
/help	Помощь по командам
/history	История последних сообщений
/knowledge	Поиск в базе знаний
/max_status	Статус интеграции с MAX

База данных
Используется PostgreSQL с SQLAlchemy ORM.

Структура проекта

MAX/
├── app/
│ ├── init.py
│ ├── database.py # Подключение к PostgreSQL (SQLAlchemy)
│ ├── models.py # Модели данных
│ ├── hh_api.py # База знаний по API hh.ru
│ ├── yandex_assistant.py # Интеграция с Yandex GPT
│ ├── telegram_bot.py # Telegram бот
│ ├── main.py # Точка входа
│ └── config.py # Настройки
├── examples/
│ ├── screenshot_bot.png # Скриншот работы бота
│ └── video.mp4 # Видео-демонстрация
├── .env.example # Пример .env файла
├── .gitignore
├── requirements.txt
└── README.md

 Скриншоты
Скриншоты работы бота находятся в папке examples/

## Запуск

### 1. Клонируйте репозиторий
```bash
git clone https://github.com/ваш_аккаунт/chatbot-max.git
cd chatbot-max

2. Создайте виртуальное окружение
python -m venv venv
venv\Scripts\activate      # Windows
# source venv/bin/activate  # Linux/Mac
3. Установите зависимости
pip install -r requirements.txt
4. Настройте .env
Скопируйте .env.example в .env и заполните:

Переменная	Описание
TELEGRAM_BOT_TOKEN	Токен бота от @BotFather
YANDEX_API_KEY	API-ключ Yandex Cloud
YANDEX_FOLDER_ID	ID каталога в Yandex Cloud
DB_HOST	Хост PostgreSQL (localhost)
DB_PORT	Порт PostgreSQL (55555)
DB_NAME	Имя базы данных
DB_USER	Пользователь PostgreSQL
DB_PASSWORD	Пароль PostgreSQL

5. Запустите PostgreSQL
net start postgresql-15

6. Запустите бота
python app/main.py
Команды бота
/start — приветствие

/help — помощь

/history — история сообщений

Автор
Евгений
