import os
import json
import logging
import requests
import yaml
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from app.models import DocFragment, KnowledgeUpdateLog
from app.database import SessionLocal
from sentence_transformers import SentenceTransformer
from app.database import SessionLocal, Base

logger = logging.getLogger(__name__)

_model = None

def get_embedding_model():
    global _model
    if _model is None:
        _model = SentenceTransformer('all-MiniLM-L6-v2')
    return _model

def create_embedding(text: str) -> List[float]:
    if not text:
        return []
    try:
        model = get_embedding_model()
        embedding = model.encode(text[:1000], normalize_embeddings=True)
        return embedding.tolist()
    except Exception as e:
        logger.error(f"Ошибка создания embedding: {e}")
        return []

class DocLoader:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*'
        })
    
    def load_openapi_from_hh(self) -> List[Dict[str, Any]]:
        """Загружает OpenAPI-спецификацию с официального источника HH.ru"""
        try:
            url = "https://api.hh.ru/openapi/specification/public"
            logger.info(f"Загрузка OpenAPI из: {url}")
            
            response = self.session.get(url, timeout=30)
            
            if response.status_code == 200:
                try:
                    spec = yaml.safe_load(response.text)
                except:
                    try:
                        spec = response.json()
                    except:
                        logger.error("Не удалось распарсить OpenAPI")
                        return []
                
                if not spec or "paths" not in spec:
                    logger.warning("OpenAPI не содержит paths")
                    return []
                
                fragments = []
                
                for path, path_item in spec.get("paths", {}).items():
                    for method, operation in path_item.items():
                        if method.lower() not in ["get", "post", "put", "delete", "patch"]:
                            continue
                        
                        summary = operation.get("summary", "")
                        description = operation.get("description", "")
                        
                        # Пропускаем слишком короткие описания
                        if len(summary) < 5 and len(description) < 10:
                            continue
                        
                        content = f"{method.upper()} {path}\n{summary}\n{description}"
                        
                        if operation.get("parameters"):
                            content += "\nПараметры:\n"
                            for param in operation["parameters"]:
                                param_name = param.get('name', '')
                                param_desc = param.get('description', '')
                                content += f"- {param_name}: {param_desc}\n"
                        
                        if operation.get("requestBody"):
                            content += f"\nТело запроса: {operation['requestBody'].get('description', '')}\n"
                        
                        # Формируем безопасный section_path
                        section_path = f"{method.upper()}_{path}".replace('/', '_').replace('{', '').replace('}', '')
                        if len(section_path) > 200:
                            section_path = section_path[:200]
                        
                        fragments.append({
                            "title": f"{method.upper()} {path}",
                            "content": content.strip(),
                            "endpoint": path,
                            "http_method": method.upper(),
                            "source_url": "https://api.hh.ru/openapi/redoc",
                            "section_path": section_path
                        })
                
                # Добавляем ключевые фрагменты, которых может не быть в OpenAPI
                self._add_missing_fragments(fragments)
                
                if fragments:
                    logger.info(f"✅ Загружено {len(fragments)} фрагментов из OpenAPI hh.ru")
                    return fragments
                else:
                    logger.warning("OpenAPI загружен, но фрагментов нет")
                    return []
            else:
                logger.warning(f"OpenAPI вернул статус {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Ошибка загрузки OpenAPI: {e}")
            return []
    
    def _add_missing_fragments(self, fragments: List[Dict[str, Any]]):
        """Добавляет явные фрагменты, которых нет в OpenAPI"""
        
        # Проверяем наличие GET /vacancies
        has_vacancies = any(
            'vacancies' in f.get('endpoint', '').lower() and 
            f.get('http_method') == 'GET' 
            for f in fragments
        )
        
        if not has_vacancies:
            fragments.append({
                "title": "GET /vacancies - Поиск вакансий",
                "content": """GET /vacancies
Поиск вакансий в API hh.ru

Возвращает список вакансий, соответствующих параметрам поиска.

Основные параметры:
- text: Текст поиска (например, "Python разработчик")
- area: ID региона (1 - Москва, 2 - Санкт-Петербург)
- experience: Опыт работы (noExperience, between1And3, between3And6, moreThan6)
- salary: Зарплата
- employment: Тип занятости (full, part, project, volunteer, probation)
- schedule: График работы (fullDay, shift, flexible, remote, flyInFlyOut)

Пример запроса:
GET https://api.hh.ru/vacancies?text=Python+разработчик&area=1

Документация: https://api.hh.ru/openapi/redoc#tag/Poisk-vakansij""",
                "endpoint": "/vacancies",
                "http_method": "GET",
                "source_url": "https://api.hh.ru/openapi/redoc#tag/Poisk-vakansij",
                "section_path": "GET_vacancies_search"
            })
            logger.info("✅ Добавлен явный фрагмент для поиска вакансий")
        
        # Проверяем наличие POST /resumes
        has_resume = any(
            'resumes' in f.get('endpoint', '').lower() and 
            f.get('http_method') == 'POST' 
            for f in fragments
        )
        
        if not has_resume:
            fragments.append({
                "title": "POST /resumes - Создание резюме",
                "content": """POST /resumes
Создание нового резюме в API hh.ru

Для создания резюме необходимо отправить POST-запрос на /resumes с данными резюме в теле запроса.

Обязательные поля:
- first_name: Имя
- last_name: Фамилия
- position: Желаемая должность
- salary: Желаемая зарплата
- experience: Опыт работы

Необязательные поля:
- about: О себе
- education: Образование
- languages: Знание языков
- skills: Навыки

Пример запроса:
POST https://api.hh.ru/resumes
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "first_name": "Иван",
  "last_name": "Иванов",
  "position": "Python разработчик",
  "salary": 150000
}

Документация: https://api.hh.ru/openapi/redoc#tag/Rezyume""",
                "endpoint": "/resumes",
                "http_method": "POST",
                "source_url": "https://api.hh.ru/openapi/redoc#tag/Rezyume",
                "section_path": "POST_resumes_create"
            })
            logger.info("✅ Добавлен явный фрагмент для создания резюме")
        
        # Проверяем наличие авторизации
        has_auth = any(
            'oauth' in f.get('endpoint', '').lower() or 
            'авторизац' in f.get('content', '').lower()
            for f in fragments
        )
        
        if not has_auth:
            fragments.append({
                "title": "POST /oauth/token - Авторизация",
                "content": """POST /oauth/token
Авторизация в API hh.ru через OAuth 2.0

Шаги для получения токена:
1. Зарегистрируйте приложение: https://dev.hh.ru/admin/
2. Получите client_id и client_secret
3. Отправьте запрос:

POST https://hh.ru/oauth/token
Content-Type: application/x-www-form-urlencoded

grant_type=authorization_code
&client_id=ваш_client_id
&client_secret=ваш_client_secret
&code=ваш_code

4. В ответ получите access_token

Документация: https://dev.hh.ru/page/authorization""",
                "endpoint": "/oauth/token",
                "http_method": "POST",
                "source_url": "https://dev.hh.ru/page/authorization",
                "section_path": "POST_oauth_token_auth"
            })
            logger.info("✅ Добавлен явный фрагмент для авторизации")
    
    def _get_fallback_fragments(self) -> List[Dict[str, Any]]:
        """Ручные фрагменты (только для первого демонстрационного наполнения)"""
        return [
            {
                "title": "GET /vacancies - Поиск вакансий",
                "content": """GET /vacancies
Поиск вакансий в API hh.ru

Параметры:
- text: Текст поиска
- area: ID региона
- experience: Опыт работы
- salary: Зарплата

Документация: https://api.hh.ru/openapi/redoc#tag/Poisk-vakansij""",
                "endpoint": "/vacancies",
                "http_method": "GET",
                "source_url": "https://api.hh.ru/openapi/redoc#tag/Poisk-vakansij",
                "section_path": "GET_vacancies_search_fallback"
            },
            {
                "title": "POST /resumes - Создание резюме",
                "content": """POST /resumes
Создание резюме в API hh.ru

POST https://api.hh.ru/resumes
Authorization: Bearer {access_token}

Документация: https://api.hh.ru/openapi/redoc#tag/Rezyume""",
                "endpoint": "/resumes",
                "http_method": "POST",
                "source_url": "https://api.hh.ru/openapi/redoc#tag/Rezyume",
                "section_path": "POST_resumes_create_fallback"
            },
            {
                "title": "POST /oauth/token - Авторизация",
                "content": """Авторизация в API hh.ru

API hh.ru использует OAuth 2.0.

POST https://hh.ru/oauth/token

Параметры:
- grant_type: authorization_code
- client_id: ID приложения
- client_secret: Секрет приложения
- code: Код авторизации

Документация: https://dev.hh.ru/page/authorization""",
                "endpoint": "/oauth/token",
                "http_method": "POST",
                "source_url": "https://dev.hh.ru/page/authorization",
                "section_path": "POST_oauth_token_auth_fallback"
            },
            {
                "title": "POST /negotiations - Отклик на вакансию",
                "content": """POST /negotiations
Отклик на вакансию в API hh.ru

POST https://api.hh.ru/negotiations
Authorization: Bearer {access_token}

Документация: https://api.hh.ru/openapi/redoc#tag/Otkliki""",
                "endpoint": "/negotiations",
                "http_method": "POST",
                "source_url": "https://api.hh.ru/openapi/redoc#tag/Otkliki",
                "section_path": "POST_negotiations_create_fallback"
            }
        ]
    
    def update_knowledge_base(self, update_type: str = "manual") -> Dict[str, Any]:
        """Обновляет базу знаний из OpenAPI"""
        log_entry = KnowledgeUpdateLog(
            update_type=update_type,
            status="started",
            started_at=datetime.now()
        )
        
        db = SessionLocal()
        try:
            db.add(log_entry)
            db.commit()
            
            # Загружаем OpenAPI с официального источника
            logger.info("🔄 Загрузка OpenAPI с hh.ru...")
            fragments = self.load_openapi_from_hh()
            
            # Если OpenAPI не загрузился — используем ручные фрагменты ТОЛЬКО для первого запуска
            if not fragments:
                existing_count = db.query(DocFragment).count()
                if existing_count == 0:
                    logger.warning("⚠️ Первый запуск: используем демонстрационные фрагменты")
                    fragments = self._get_fallback_fragments()
                else:
                    logger.error("❌ OpenAPI не загрузился, но в БД есть данные. Обновление отменено.")
                    log_entry.status = "failed"
                    log_entry.error_message = "OpenAPI не загрузился"
                    db.commit()
                    return {"status": "failed", "error": "OpenAPI не загрузился. База знаний не обновлена."}
            
            if not fragments:
                log_entry.status = "failed"
                log_entry.error_message = "Не удалось загрузить документацию"
                db.commit()
                return {"status": "failed", "error": "Не удалось загрузить документацию"}
            
            logger.info(f"📚 Загружено {len(fragments)} фрагментов")
            
            # Получаем существующие фрагменты
            existing = {f.section_path: f for f in db.query(DocFragment).filter(
                DocFragment.is_active == True
            ).all()}
            
            added = 0
            updated = 0
            deactivated = 0
            
            for frag_data in fragments:
                section_path = frag_data["section_path"]
                content = frag_data["content"]
                
                if section_path in existing:
                    if existing[section_path].content != content:
                        existing[section_path].content = content
                        existing[section_path].updated_at = datetime.now()
                        existing[section_path].embedding = create_embedding(content)
                        updated += 1
                else:
                    fragment = DocFragment(
                        title=frag_data["title"],
                        content=content,
                        endpoint=frag_data["endpoint"],
                        http_method=frag_data["http_method"],
                        source_url=frag_data["source_url"],
                        section_path=section_path,
                        embedding=create_embedding(content),
                        is_active=True
                    )
                    db.add(fragment)
                    added += 1
            
            # Деактивируем удалённые фрагменты
            current_paths = set(f["section_path"] for f in fragments)
            for path, fragment in existing.items():
                if path not in current_paths:
                    fragment.is_active = False
                    fragment.updated_at = datetime.now()
                    deactivated += 1
            
            db.commit()
            
            log_entry.status = "success"
            log_entry.completed_at = datetime.now()
            log_entry.fragments_added = added
            log_entry.fragments_updated = updated
            log_entry.fragments_deactivated = deactivated
            db.commit()
            
            return {
                "status": "success",
                "added": added,
                "updated": updated,
                "deactivated": deactivated,
                "total": db.query(DocFragment).filter(DocFragment.is_active == True).count()
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка обновления базы знаний: {e}")
            log_entry.status = "failed"
            log_entry.error_message = str(e)
            db.commit()
            return {"status": "failed", "error": str(e)}
        finally:
            db.close()