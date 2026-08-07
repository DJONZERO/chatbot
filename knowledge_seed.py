from app.database import SessionLocal, init_db
from app.models import Knowledge

def seed_knowledge():
    init_db()
    db = SessionLocal()
    
    knowledge_data = [
        {
            "title": "Авторизация в API hh.ru",
            "content": "API hh.ru использует OAuth 2.0. Получите токен через https://hh.ru/oauth/token",
            "category": "API hh.ru"
        },
        {
            "title": "Поиск вакансий",
            "content": "GET https://api.hh.ru/vacancies?text=Python&area=1",
            "category": "API hh.ru"
        },
        {
            "title": "Создание резюме",
            "content": "POST https://api.hh.ru/resumes с токеном авторизации",
            "category": "API hh.ru"
        },
        {
            "title": "Отклик на вакансию",
            "content": "POST https://api.hh.ru/negotiations с vacancy_id и resume_id",
            "category": "API hh.ru"
        },
        {
            "title": "Список регионов",
            "content": "GET https://api.hh.ru/areas для получения списка регионов",
            "category": "API hh.ru"
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