import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import MetaData, text
from app.database import engine
from app.models import Base

def clean_and_create():
    with engine.connect() as conn:
        # Удаляем таблицы через сырой SQL
        conn.execute(text("DROP TABLE IF EXISTS knowledge_update_logs CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS doc_fragments CASCADE"))
        conn.commit()
        
        # Очищаем метаданные
        Base.metadata.clear()
        
        # Создаём таблицы заново
        Base.metadata.create_all(engine)
        print("✅ Таблицы созданы")

if __name__ == "__main__":
    clean_and_create()