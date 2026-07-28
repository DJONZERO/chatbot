from app.database import SessionLocal, init_db
from app.models import Knowledge

def seed_knowledge():
    init_db()
    db = SessionLocal()
    
    knowledge_data = [
        {
            "title": "Что такое MAX",
            "content": "MAX - платформа для чат-ботов.",
            "category": "Общее"
        },
        {
            "title": "Yandex GPT",
            "content": "Нейросеть для генерации текста.",
            "category": "Технологии"
        },
        {
            "title": "Как задать вопрос",
            "content": "Напишите сообщение в чат.",
            "category": "Использование"
        }
    ]
    
    for data in knowledge_data:
        existing = db.query(Knowledge).filter(Knowledge.title == data["title"]).first()
        if not existing:
            knowledge = Knowledge(
                title=data["title"],
                content=data["content"],
                category=data["category"]
            )
            db.add(knowledge)
    
    db.commit()
    print("✅ База знаний заполнена!")
    db.close()

if __name__ == "__main__":
    seed_knowledge()