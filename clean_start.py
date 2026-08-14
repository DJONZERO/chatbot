import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 1. Сначала удаляем таблицы через сырой SQL (без моделей)
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

# Удаляем таблицы
with engine.connect() as conn:
    conn.execute(text("DROP TABLE IF EXISTS knowledge_update_logs CASCADE"))
    conn.execute(text("DROP TABLE IF EXISTS doc_fragments CASCADE"))
    conn.commit()
    print("✅ Таблицы удалены из БД")

# 2. Теперь импортируем модели и создаём таблицы
from app.database import Base
from app.models import DocFragment, KnowledgeUpdateLog

# Очищаем метаданные
Base.metadata.clear()

# Создаём таблицы
Base.metadata.create_all(engine)
print("✅ Таблицы созданы с pgvector")