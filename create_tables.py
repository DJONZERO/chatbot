from app.database import init_db

if __name__ == "__main__":
    print("🔄 Создание таблиц...")
    init_db()
    print("✅ Таблицы созданы!")