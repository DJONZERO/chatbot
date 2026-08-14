from app.database import engine
from app.models import Base
from sqlalchemy import text

# 1. Очищаем таблицу
with engine.connect() as conn:
    conn.execute(text("TRUNCATE TABLE doc_fragments RESTART IDENTITY CASCADE"))
    conn.commit()
    print("✅ Таблица doc_fragments очищена")

# 2. Проверяем тип поля
with engine.connect() as conn:
    result = conn.execute(text("SELECT data_type FROM information_schema.columns WHERE table_name = 'doc_fragments' AND column_name = 'embedding'"))
    data_type = result.scalar()
    print(f"Тип поля embedding: {data_type}")
    
    if data_type and data_type.lower() in ('vector', 'USER-DEFINED'):
        print("✅ Поле embedding имеет тип vector")
    else:
        print(f"❌ Ошибка! Тип поля: {data_type}")

# 3. Заполняем базу знаний
from app.doc_loader import DocLoader
dl = DocLoader()
result = dl.update_knowledge_base(update_type='manual')
print(result)