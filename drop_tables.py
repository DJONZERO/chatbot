import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import engine
from app.models import DocFragment, KnowledgeUpdateLog
from sqlalchemy import text

def drop_tables():
    """Удаляет таблицы RAG"""
    try:
        with engine.connect() as conn:
            conn.execute(text("DROP TABLE IF EXISTS knowledge_update_logs CASCADE"))
            conn.execute(text("DROP TABLE IF EXISTS doc_fragments CASCADE"))
            conn.commit()
            print("✅ Таблицы удалены")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    drop_tables()