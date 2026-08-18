import os
import logging
from typing import List, Dict, Any
from dotenv import load_dotenv
from app.retriever import Retriever
from app.database import SessionLocal

load_dotenv()

logger = logging.getLogger(__name__)

class YandexAssistant:
    def __init__(self):
        self.retriever = Retriever()
        self.mode = "hybrid_search"
        logger.info("✅ Assistant инициализирован (режим гибридного поиска)")
    
    def generate_response(self, prompt: str) -> str:
        """Генерирует ответ на основе найденных фрагментов"""
        
        db = SessionLocal()
        try:
            fragments = self.retriever.search(db, prompt)
            logger.info(f"🔍 Найдено {len(fragments)} фрагментов для запроса: {prompt[:50]}")
            
            if not fragments:
                return self._no_info_response()
            
            return self._build_response_from_fragments(prompt, fragments)
                
        except Exception as e:
            logger.error(f"❌ Ошибка в generate_response: {e}")
            import traceback
            traceback.print_exc()
            return f"Произошла ошибка при обработке запроса: {str(e)}"
        finally:
            db.close()
    
    def _escape_markdown(self, text: str) -> str:
        """Экранирует специальные символы для Telegram Markdown"""
        if not text:
            return ""
        special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        for char in special_chars:
            text = text.replace(char, f'\\{char}')
        return text
    
    def _build_response_from_fragments(self, prompt: str, fragments: List[Dict[str, Any]]) -> str:
        """Строит ответ из найденных фрагментов"""
        
        topic = self._detect_topic(prompt)
        
        response = f"📚 **Найдена информация по вашему запросу:**\n\n"
        response += f"**Тема:** {topic}\n\n"
        
        for i, f in enumerate(fragments[:5], 1):
            title = self._escape_markdown(f.get('title', 'Без названия'))
            response += f"**{i}. {title}**\n"
            
            if f.get('http_method') and f.get('endpoint'):
                method = self._escape_markdown(f['http_method'])
                endpoint = self._escape_markdown(f['endpoint'])
                response += f"🔧 **Метод:** `{method} {endpoint}`\n"
            
            content = f.get('content', '')
            if len(content) > 600:
                content = content[:600] + "..."
            content = self._escape_markdown(content)
            response += f"📝 **Описание:**\n```\n{content}\n```\n"
            
            if f.get('similarity'):
                similarity = f['similarity'] * 100
                response += f"📊 **Релевантность:** {similarity:.1f}%\n"
            
            if f.get('source_url'):
                source_url = self._escape_markdown(f['source_url'])
                response += f"📖 **Источник:** {source_url}\n"
            
            response += "\n---\n\n"
        
        response += "💡 **Используйте эти эндпоинты из официальной документации hh.ru.**\n"
        response += "📖 **Общая документация:** https://api.hh.ru/openapi/redoc"
        
        if len(response) > 4000:
            response = response[:3997] + "..."
        
        return response
    
    def _detect_topic(self, prompt: str) -> str:
        """Определяет тему вопроса"""
        prompt_lower = prompt.lower()
        
        topics = {
            'вакансии': 'Поиск и работа с вакансиями',
            'вакансия': 'Поиск и работа с вакансиями',
            'vacancy': 'Поиск и работа с вакансиями',
            'резюме': 'Поиск и работа с резюме',
            'resume': 'Поиск и работа с резюме',
            'авторизация': 'Авторизация и OAuth',
            'токен': 'Авторизация и OAuth',
            'oauth': 'Авторизация и OAuth',
            'auth': 'Авторизация и OAuth',
            'отклик': 'Отклики на вакансии',
            'negotiation': 'Отклики на вакансии',
            'работодатель': 'Работа с работодателями',
            'employer': 'Работа с работодателями',
            'поиск': 'Поиск',
            'создание': 'Создание',
            'create': 'Создание',
            'обновление': 'Обновление',
            'update': 'Обновление',
            'удаление': 'Удаление',
            'delete': 'Удаление'
        }
        
        for key, value in topics.items():
            if key in prompt_lower:
                return value
        
        return 'API hh.ru'
    
    def _no_info_response(self) -> str:
        """Ответ при отсутствии информации"""
        return """❌ **Информация не найдена**

К сожалению, в документации API hh.ru не найдена информация по вашему запросу.

**Рекомендации:**
1. Попробуйте переформулировать вопрос
2. Используйте ключевые слова: вакансии, резюме, авторизация, отклик
3. Обратитесь к официальной документации:
   📖 https://api.hh.ru/openapi/redoc
   📖 https://dev.hh.ru

**Примеры правильных вопросов:**
- "Как найти вакансии?"
- "Как авторизоваться в API?"
- "Как создать резюме?"
- "Как откликнуться на вакансию?"""