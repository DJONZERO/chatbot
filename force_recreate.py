from app.database import engine
from app.models import Base
from sqlalchemy import text

with engine.connect() as conn:
    # Удаляем таблицу принудительно
    conn.execute(text("DROP TABLE IF EXISTS doc_fragments CASCADE"))
    conn.commit()
    print("✅ Таблица удалена")

# Создаём таблицы заново
Base.metadata.create_all(engine)
print("✅ Таблицы созданы с Vector")

# Проверяем тип поля
with engine.connect() as conn:
    result = conn.execute(text("SELECT data_type FROM information_schema.columns WHERE table_name = 'doc_fragments' AND column_name = 'embedding'"))
    print(f"Тип поля embedding: {result.scalar()}")from app.database import engine
from app.models import Base
from sqlalchemy import text

# 1. Удаляем таблицу принудительно
with engine.connect() as conn:
    conn.execute(text("DROP TABLE IF EXISTS doc_fragments CASCADE"))
    conn.commit()
    print("✅ Таблица doc_fragments удалена")

# 2. Очищаем метаданные SQLAlchemy
Base.metadata.clear()

# 3. Создаём таблицы заново
Base.metadata.create_all(engine)
print("✅ Таблицы созданы")

# 4. Проверяем тип поля
with engine.connect() as conn:
    result = conn.execute(text("SELECT data_type FROM information_schema.columns WHERE table_name = 'doc_fragments' AND column_name = 'embedding'"))
    data_type = result.scalar()
    print(f"Тип поля embedding: {data_type}")
    
    if data_type and data_type.lower() in ('vector', 'USER-DEFINED'):
        print("✅ Успешно! Поле embedding имеет тип vector")
    else:
        print(f"❌ Ошибка! Тип поля: {data_type}")