import os
import json
import logging
import requests
import re
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from app.models import DocFragment, KnowledgeUpdateLog
from app.database import SessionLocal
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

_model = None

def get_embedding_model():
    global _model
    if _model is None:
        _model = SentenceTransformer('all-MiniLM-L6-v2')
    return _model

def create_embedding(text: str) -> List[float]:
    if not text:
        return None
    model = get_embedding_model()
    embedding = model.encode(text[:1000])
    return embedding.tolist()

class DocLoader:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*'
        })
    
    def load_openapi_from_hh(self) -> List[Dict[str, Any]]:
        """Загружает и парсит OpenAPI-спецификацию с hh.ru"""
        try:
            urls = [
                "https://api.hh.ru/openapi/redoc?format=json",
                "https://api.hh.ru/openapi/redoc?format=yaml",
            ]
            
            for url in urls:
                try:
                    logger.info(f"Загрузка OpenAPI из: {url}")
                    response = self.session.get(url, timeout=30)
                    
                    if response.status_code == 200:
                        # Пробуем парсить как JSON
                        try:
                            spec = response.json()
                        except:
                            # Если не JSON, пробуем YAML
                            import yaml
                            spec = yaml.safe_load(response.text)
                        
                        if not spec or "paths" not in spec:
                            logger.warning("OpenAPI не содержит paths")
                            continue
                        
                        fragments = []
                        
                        for path, path_item in spec.get("paths", {}).items():
                            for method, operation in path_item.items():
                                if method.lower() not in ["get", "post", "put", "delete", "patch"]:
                                    continue
                                
                                summary = operation.get("summary", "")
                                description = operation.get("description", "")
                                
                                content = f"{method.upper()} {path}\n{summary}\n{description}"
                                
                                if operation.get("parameters"):
                                    content += "\nПараметры:\n"
                                    for param in operation["parameters"]:
                                        param_name = param.get('name', '')
                                        param_desc = param.get('description', '')
                                        content += f"- {param_name}: {param_desc}\n"
                                
                                if operation.get("requestBody"):
                                    content += f"\nТело запроса: {operation['requestBody'].get('description', '')}\n"
                                
                                fragments.append({
                                    "title": f"{method.upper()} {path}",
                                    "content": content.strip(),
                                    "endpoint": path,
                                    "http_method": method.upper(),
                                    "source_url": "https://api.hh.ru/openapi/redoc",
                                    "section_path": f"{method.upper()}_{path}".replace('/', '_')
                                })
                        
                        if fragments:
                            logger.info(f"✅ Загружено {len(fragments)} фрагментов из OpenAPI hh.ru")
                            return fragments
                        else:
                            logger.warning("OpenAPI загружен, но фрагментов нет")
                    
                except Exception as e:
                    logger.warning(f"Ошибка загрузки {url}: {e}")
                    continue
            
            return []
            
        except Exception as e:
            logger.error(f"Ошибка загрузки OpenAPI: {e}")
            return []
    
    def load_from_github(self) -> List[Dict[str, Any]]:
        """Загружает документацию из GitHub репозитория hhru/api"""
        fragments = []
        
        github_urls = [
            "https://raw.githubusercontent.com/hhru/api/master/docs/openapi.yaml",
            "https://raw.githubusercontent.com/hhru/api/master/openapi.yml",
            "https://raw.githubusercontent.com/hhru/api/master/docs/openapi.json",
        ]
        
        for url in github_urls:
            try:
                logger.info(f"Загрузка из GitHub: {url}")
                response = self.session.get(url, timeout=30)
                if response.status_code == 200:
                    content = response.text
                    # Ищем пути в YAML/JSON
                    paths = re.findall(r'/([a-z]+(?:_[a-z]+)*):', content)
                    if paths:
                        for path in set(paths[:20]):
                            fragments.append({
                                "title": f"API метод /{path}",
                                "content": f"Документация API hh.ru: /{path}\nЭндпоинт: https://api.hh.ru/{path}",
                                "endpoint": f"/{path}",
                                "http_method": "GET",
                                "source_url": url,
                                "section_path": f"github_{path}"
                            })
                        if fragments:
                            logger.info(f"Загружено {len(fragments)} фрагментов из GitHub")
                            return fragments
            except Exception as e:
                logger.warning(f"Не удалось загрузить {url}: {e}")
        
        return fragments
    
    def _get_fallback_fragments(self) -> List[Dict[str, Any]]:
        """Ручные фрагменты (запасной вариант)"""
        return [
            {
                "title": "Авторизация в API hh.ru",
                "content": """Авторизация в API hh.ru

API hh.ru использует OAuth 2.0.

Шаги для получения токена:
1. Зарегистрируйте приложение: https://dev.hh.ru/admin/
2. Получите client_id и client_secret
3. Отправьте запрос на получение токена:

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
                "section_path": "Авторизация"
            },
            {
                "title": "Поиск вакансий",
                "content": """Поиск вакансий в API hh.ru

GET https://api.hh.ru/vacancies

Параметры:
- text — Текст поиска
- area — ID региона (1 — Москва)
- experience — Опыт работы
- salary — Зарплата

Документация: https://api.hh.ru/openapi/redoc#tag/Poisk-vakansij""",
                "endpoint": "/vacancies",
                "http_method": "GET",
                "source_url": "https://api.hh.ru/openapi/redoc#tag/Poisk-vakansij",
                "section_path": "Поиск_вакансий"
            },
            {
                "title": "Создание резюме",
                "content": """Создание резюме в API hh.ru

POST https://api.hh.ru/resumes
Authorization: Bearer {access_token}

Документация: https://api.hh.ru/openapi/redoc#tag/Rezyume""",
                "endpoint": "/resumes",
                "http_method": "POST",
                "source_url": "https://api.hh.ru/openapi/redoc#tag/Rezyume",
                "section_path": "Создание_резюме"
            },
            {
                "title": "Отклик на вакансию",
                "content": """Отклик на вакансию в API hh.ru

POST https://api.hh.ru/negotiations
Authorization: Bearer {access_token}

Документация: https://api.hh.ru/openapi/redoc#tag/Otkliki""",
                "endpoint": "/negotiations",
                "http_method": "POST",
                "source_url": "https://api.hh.ru/openapi/redoc#tag/Otkliki",
                "section_path": "Отклик_на_вакансию"
            }
        ]
    
    def update_knowledge_base(self, update_type: str = "manual") -> Dict[str, Any]:
        """Обновляет базу знаний из OpenAPI и GitHub"""
        log_entry = KnowledgeUpdateLog(
            update_type=update_type,
            status="started",
            started_at=datetime.now()
        )
        
        db = SessionLocal()
        try:
            db.add(log_entry)
            db.commit()
            
            # 1. Сначала пробуем загрузить OpenAPI с hh.ru
            logger.info("🔄 Загрузка OpenAPI с hh.ru...")
            fragments = self.load_openapi_from_hh()
            
            # 2. Если OpenAPI не загрузился — пробуем GitHub
            if not fragments:
                logger.info("🔄 OpenAPI не загружен, пробуем GitHub...")
                fragments = self.load_from_github()
            
            # 3. Если ничего не загрузилось — используем ручные фрагменты
            if not fragments:
                logger.warning("⚠️ Используем ручные фрагменты")
                fragments = self._get_fallback_fragments()
            
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