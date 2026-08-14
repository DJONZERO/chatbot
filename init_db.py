from app.database import engine
from app.models import Base
from sqlalchemy import text

# Проверяем, что таблицы нет
with engine.connect() as conn:
    result = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_name = 'doc_fragments'"))
    if result.scalar():
        print("❌ Таблица всё ещё существует. Удалите её вручную через pgAdmin.")
    else:
        print("✅ Таблицы нет. Создаём...")
        Base.metadata.create_all(engine)
        print("✅ Таблицы созданы")