import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

# Берём параметры из .env
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "55555")
DB_NAME = os.getenv("DB_NAME", "chatbot_db")
DB_USER = os.getenv("DB_USER", "chatbot_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "chatbot_password")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DATABASE_URL)

try:
    with engine.connect() as conn:
        # Проверяем, существует ли расширение
        result = conn.execute(text("SELECT 1 FROM pg_extension WHERE extname = 'vector'"))
        if result.scalar():
            print("✅ Расширение vector уже установлено")
        else:
            # Создаём расширение
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            conn.commit()
            print("✅ Расширение vector создано")
            
        # Проверяем, что расширение работает
        result = conn.execute(text("SELECT '[]'::vector"))
        print("✅ Расширение vector работает")
except Exception as e:
    print(f"❌ Ошибка: {e}")
    print("\nУбедитесь, что:")
    print("1. PostgreSQL запущен")
    print("2. Пользователь chatbot_user существует")
    print("3. База данных chatbot_db существует")