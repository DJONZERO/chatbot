from app.database import SessionLocal
from app.models import DocFragment
from app.doc_loader import create_embedding

db = SessionLocal()

manual_fragments = [
    {
        'title': 'Авторизация в API hh.ru',
        'content': 'Авторизация в API hh.ru\n\nAPI hh.ru использует OAuth 2.0.\n\nШаги:\n1. Зарегистрируйте приложение: https://dev.hh.ru/admin/\n2. Получите client_id и client_secret\n3. Отправьте запрос на получение токена\n\nPOST https://hh.ru/oauth/token\nContent-Type: application/x-www-form-urlencoded\n\ngrant_type=authorization_code\n&client_id=ваш_client_id\n&client_secret=ваш_client_secret\n&code=ваш_code\n\n4. В ответ получите access_token\n\nДокументация: https://dev.hh.ru/page/authorization',
        'endpoint': '/oauth/token',
        'http_method': 'POST',
        'source_url': 'https://dev.hh.ru/page/authorization',
        'section_path': 'Авторизация'
    },
    {
        'title': 'Поиск вакансий',
        'content': 'Поиск вакансий в API hh.ru\n\nGET https://api.hh.ru/vacancies\n\nПараметры:\n- text — Текст поиска\n- area — ID региона\n- experience — Опыт работы\n- salary — Зарплата\n\nДокументация: https://api.hh.ru/openapi/redoc#tag/Poisk-vakansij',
        'endpoint': '/vacancies',
        'http_method': 'GET',
        'source_url': 'https://api.hh.ru/openapi/redoc#tag/Poisk-vakansij',
        'section_path': 'Поиск_вакансий'
    },
    {
        'title': 'Создание резюме',
        'content': 'Создание резюме в API hh.ru\n\nPOST https://api.hh.ru/resumes\nAuthorization: Bearer {access_token}\n\nДокументация: https://api.hh.ru/openapi/redoc#tag/Rezyume',
        'endpoint': '/resumes',
        'http_method': 'POST',
        'source_url': 'https://api.hh.ru/openapi/redoc#tag/Rezyume',
        'section_path': 'Создание_резюме'
    },
    {
        'title': 'Отклик на вакансию',
        'content': 'Отклик на вакансию в API hh.ru\n\nPOST https://api.hh.ru/negotiations\nAuthorization: Bearer {access_token}\n\nДокументация: https://api.hh.ru/openapi/redoc#tag/Otkliki',
        'endpoint': '/negotiations',
        'http_method': 'POST',
        'source_url': 'https://api.hh.ru/openapi/redoc#tag/Otkliki',
        'section_path': 'Отклик_на_вакансию'
    }
]

for data in manual_fragments:
    existing = db.query(DocFragment).filter(DocFragment.section_path == data['section_path']).first()
    if not existing:
        fragment = DocFragment(
            title=data['title'],
            content=data['content'],
            endpoint=data['endpoint'],
            http_method=data['http_method'],
            source_url=data['source_url'],
            section_path=data['section_path'],
            embedding=create_embedding(data['content']),
            is_active=True
        )
        db.add(fragment)
        print(f'✅ Добавлен: {data["title"]}')
    else:
        print(f'⏭️ Уже существует: {data["title"]}')

db.commit()
db.close()

print('✅ Готово!')