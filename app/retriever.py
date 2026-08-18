import os
import logging
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.models import DocFragment
from app.doc_loader import create_embedding

logger = logging.getLogger(__name__)

class Retriever:
    def __init__(self):
        self.similarity_threshold = float(os.getenv("SIMILARITY_THRESHOLD", "0.1"))
        self.max_fragments = int(os.getenv("MAX_RAG_FRAGMENTS", "5"))
        logger.info(f"🔍 Retriever инициализирован: порог={self.similarity_threshold}, максимум={self.max_fragments}")
    
    def search(self, db: Session, query: str) -> List[Dict[str, Any]]:
        """
        Векторный поиск через pgvector с косинусным расстоянием (<=>)
        Релевантность = 1 - cosine_distance
        """
        query_lower = query.lower()
        
        # Проверка на нерелевантные запросы
        irrelevant_keywords = ['погода', 'weather', 'сегодня', 'завтра', 'вчера', 'температура']
        if any(word in query_lower for word in irrelevant_keywords):
            logger.info(f"⚠️ Нерелевантный запрос: {query}")
            return []
        
        # ===== СПЕЦИАЛЬНЫЕ ПРОВЕРКИ ДЛЯ КЛЮЧЕВЫХ ЗАПРОСОВ =====
        # 1. Авторизация
        if 'авториз' in query_lower or 'токен' in query_lower or 'oauth' in query_lower:
            auth_fragment = db.query(DocFragment).filter(
                DocFragment.is_active == True,
                DocFragment.endpoint == '/oauth/token',
                DocFragment.http_method == 'POST'
            ).first()
            if auth_fragment:
                logger.info(f"🔑 Найден фрагмент авторизации: {auth_fragment.title}")
                return [{
                    "id": auth_fragment.id,
                    "title": auth_fragment.title,
                    "content": auth_fragment.content,
                    "endpoint": auth_fragment.endpoint,
                    "http_method": auth_fragment.http_method,
                    "source_url": auth_fragment.source_url,
                    "similarity": 1.0
                }]
        
        # 2. Поиск вакансий
        if 'ваканс' in query_lower and ('найти' in query_lower or 'поиск' in query_lower):
            vacancy_fragment = db.query(DocFragment).filter(
                DocFragment.is_active == True,
                DocFragment.endpoint == '/vacancies',
                DocFragment.http_method == 'GET'
            ).first()
            if vacancy_fragment:
                logger.info(f"🔍 Найден фрагмент поиска вакансий: {vacancy_fragment.title}")
                return [{
                    "id": vacancy_fragment.id,
                    "title": vacancy_fragment.title,
                    "content": vacancy_fragment.content,
                    "endpoint": vacancy_fragment.endpoint,
                    "http_method": vacancy_fragment.http_method,
                    "source_url": vacancy_fragment.source_url,
                    "similarity": 1.0
                }]
        
        # 3. Создание резюме
        if 'резюме' in query_lower and ('создать' in query_lower or 'создание' in query_lower):
            resume_fragment = db.query(DocFragment).filter(
                DocFragment.is_active == True,
                DocFragment.endpoint == '/resumes',
                DocFragment.http_method == 'POST'
            ).first()
            if resume_fragment:
                logger.info(f"📄 Найден фрагмент создания резюме: {resume_fragment.title}")
                return [{
                    "id": resume_fragment.id,
                    "title": resume_fragment.title,
                    "content": resume_fragment.content,
                    "endpoint": resume_fragment.endpoint,
                    "http_method": resume_fragment.http_method,
                    "source_url": resume_fragment.source_url,
                    "similarity": 1.0
                }]
        # ======================================================
        
        # ===== ОСНОВНОЙ ВЕКТОРНЫЙ ПОИСК =====
        # Сначала пробуем векторный поиск
        vector_results = self._vector_search(db, query)
        if vector_results:
            logger.info(f"✅ Векторный поиск нашел {len(vector_results)} фрагментов")
            return vector_results[:self.max_fragments]
        # =====================================
        
        # Если векторный не дал результатов, пробуем текстовый (резервный)
        logger.info("🔄 Векторный поиск не дал результатов, пробуем текстовый...")
        text_results = self._text_search(db, query)
        if text_results:
            logger.info(f"✅ Текстовый поиск нашел {len(text_results)} фрагментов")
            return text_results[:self.max_fragments]
        
        logger.warning("❌ Поиск не дал результатов")
        return []
    
    def _vector_search(self, db: Session, query: str) -> List[Dict[str, Any]]:
        """Векторный поиск через pgvector с косинусным расстоянием (<=>)"""
        # 1. Создаем embedding для запроса
        query_embedding = create_embedding(query)
        
        if not query_embedding or not isinstance(query_embedding, list) or len(query_embedding) == 0:
            logger.warning("⚠️ Не удалось создать embedding для запроса")
            return []
        
        # 2. Преобразуем в строку для PostgreSQL
        query_embedding_str = '[' + ','.join(str(float(x)) for x in query_embedding) + ']'
        
        try:
            # 3. Векторный поиск с косинусным расстоянием (<=>)
            # Релевантность = 1 - расстояние
            sql = text("""
                SELECT 
                    id, title, content, endpoint, http_method, source_url,
                    1 - (embedding <=> CAST(:embedding AS vector)) AS similarity
                FROM doc_fragments
                WHERE is_active = true AND embedding IS NOT NULL
                ORDER BY embedding <=> CAST(:embedding AS vector)
                LIMIT :limit
            """)
            
            results = db.execute(
                sql,
                {
                    "embedding": query_embedding_str,
                    "limit": self.max_fragments * 2
                }
            ).fetchall()
            
            # 4. Фильтруем по порогу релевантности
            fragments = []
            for row in results:
                similarity = float(row[6]) if row[6] is not None else 0.0
                
                if similarity >= self.similarity_threshold:
                    fragments.append({
                        "id": row[0],
                        "title": row[1],
                        "content": row[2],
                        "endpoint": row[3],
                        "http_method": row[4],
                        "source_url": row[5],
                        "similarity": similarity  # Релевантность = 1 - distance
                    })
            
            logger.info(f"🔍 Векторный поиск: найдено {len(fragments)} фрагментов")
            return fragments[:self.max_fragments]
            
        except Exception as e:
            logger.error(f"❌ Ошибка векторного поиска: {e}")
            return []
    
    def _text_search(self, db: Session, query: str) -> List[Dict[str, Any]]:
        """Текстовый поиск (резервный, для случаев когда векторный не работает)"""
        query_lower = query.lower()
        
        # Определяем ключевые слова в запросе
        keywords = []
        if 'ваканс' in query_lower or 'vacancy' in query_lower:
            keywords.append(('вакансии', ['/vacancies']))
        if 'резюме' in query_lower or 'resume' in query_lower:
            keywords.append(('резюме', ['/resumes']))
        if ('авториз' in query_lower or 'токен' in query_lower or 
            'oauth' in query_lower or 'auth' in query_lower):
            keywords.append(('авторизация', ['/oauth/token', '/oauth']))
        if 'отклик' in query_lower or 'negotiation' in query_lower:
            keywords.append(('отклик', ['/negotiations']))
        
        if not keywords:
            return []
        
        results = []
        for keyword, patterns in keywords:
            for pattern in patterns:
                fragments = db.query(DocFragment).filter(
                    DocFragment.is_active == True,
                    DocFragment.endpoint.ilike(f'%{pattern}%')
                ).all()
                
                for f in fragments:
                    if any(r['id'] == f.id for r in results):
                        continue
                    
                    similarity = 0.5
                    
                    # Точное совпадение эндпоинта — высокий приоритет
                    if f.endpoint and f.endpoint == pattern:
                        similarity += 0.5
                    elif f.endpoint and pattern in f.endpoint:
                        similarity += 0.2
                    
                    # Приоритет для методов
                    if 'создать' in query_lower and f.http_method == 'POST':
                        similarity += 0.3
                    if 'найти' in query_lower and f.http_method == 'GET':
                        similarity += 0.2
                    
                    if f.title and keyword in f.title.lower():
                        similarity += 0.2
                    
                    results.append({
                        "id": f.id,
                        "title": f.title,
                        "content": f.content,
                        "endpoint": f.endpoint,
                        "http_method": f.http_method,
                        "source_url": f.source_url,
                        "similarity": min(similarity, 1.0)
                    })
        
        results.sort(key=lambda x: x["similarity"], reverse=True)
        filtered = [r for r in results if r["similarity"] >= self.similarity_threshold]
        
        if filtered:
            logger.info(f"🔍 Текстовый поиск: найдено {len(filtered)} фрагментов")
        
        return filtered[:self.max_fragments]
    
    def build_context(self, fragments: List[Dict[str, Any]]) -> str:
        """
        Формирует контекст для Yandex GPT из найденных фрагментов
        Включает только фрагменты, прошедшие SIMILARITY_THRESHOLD
        """
        if not fragments:
            return None
        
        context_parts = []
        for i, f in enumerate(fragments, 1):
            part = f"--- ФРАГМЕНТ {i} ---\n"
            part += f"Название: {f['title']}\n"
            part += f"Содержание:\n{f['content']}\n"
            if f.get('http_method') and f.get('endpoint'):
                part += f"Метод: {f['http_method']} {f['endpoint']}\n"
            if f.get('source_url'):
                part += f"Источник: {f['source_url']}\n"
            if f.get('similarity'):
                part += f"Релевантность: {f['similarity']:.2%}\n"
            part += "---\n"
            context_parts.append(part)
        
        return "\n".join(context_parts)