from app.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    # Проверяем тип поля embedding
    result = conn.execute(text("SELECT data_type FROM information_schema.columns WHERE table_name = 'doc_fragments' AND column_name = 'embedding'"))
    data_type = result.scalar()
    print(f'Тип поля embedding: {data_type}')
    
    # Проверяем, что расширение vector установлено
    result = conn.execute(text("SELECT extname FROM pg_extension WHERE extname = 'vector'"))
    ext = result.scalar()
    print(f'Расширение vector: {ext}')
    
    if data_type and data_type.lower() in ('vector', 'USER-DEFINED'):
        print('✅ Поле embedding имеет тип vector!')
    else:
        print('❌ Поле embedding НЕ имеет тип vector. Текущий тип:', data_type)