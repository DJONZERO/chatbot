import sys
import os
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import init_db
from app.doc_loader import DocLoader

def main():
    print("=" * 50)
    print("🔄 ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ")
    print("=" * 50)
    
    print("\n1️⃣ Инициализация базы данных...")
    init_db()
    print("✅ База данных инициализирована")
    
    print("\n2️⃣ Загрузка базы знаний...")
    loader = DocLoader()
    result = loader.update_knowledge_base(update_type="manual")
    
    if result["status"] == "success":
        print(f"\n✅ База знаний успешно загружена!")
        print(f"   📊 Результаты:")
        print(f"   - Добавлено: {result['added']} фрагментов")
        print(f"   - Обновлено: {result['updated']} фрагментов")
        print(f"   - Деактивировано: {result['deactivated']} фрагментов")
        print(f"   - Всего активных: {result['total']}")
    else:
        print(f"\n❌ Ошибка загрузки: {result.get('error', 'Неизвестная ошибка')}")
    
    print("\n" + "=" * 50)
    print("✅ Готово! Теперь можно запускать бота: python -m app.main")
    print("=" * 50)

if __name__ == "__main__":
    main()