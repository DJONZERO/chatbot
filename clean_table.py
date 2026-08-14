from app.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    conn.execute(text("DROP TABLE IF EXISTS doc_fragments CASCADE"))
    conn.commit()
    print("✅ Таблица удалена")