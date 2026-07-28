import os
import logging
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class YandexAssistant:
    def __init__(self):
        self.api_key = os.getenv("YANDEX_API_KEY")
        self.folder_id = os.getenv("YANDEX_FOLDER_ID")
        self.model = os.getenv("YANDEX_MODEL", "general")
        self.base_url = "https://llm.api.cloud.yandex.net/v2"
        self.use_yandex = False  # Режим заглушки
        
        # Проверяем наличие ключей
        if self.api_key and self.folder_id:
            self.use_yandex = True
            logger.info("✅ Yandex Assistant инициализирован (режим API)")
        else:
            logger.warning("⚠️ Yandex Assistant работает в режиме заглушки (нет API ключей)")
    
    def generate_response(self, prompt: str, context: Optional[str] = None) -> str:
        """Генерация ответа (заглушка)"""
        
        # Если режим заглушки - возвращаем простой ответ
        if not self.use_yandex:
            return self._get_stub_response(prompt)
        
        # Если есть ключи - пробуем использовать Yandex GPT
        try:
            return self._generate_with_yandex(prompt, context)
        except Exception as e:
            logger.error(f"Ошибка Yandex API: {e}")
            return self._get_stub_response(prompt)
    
    def _generate_with_yandex(self, prompt: str, context: Optional[str] = None) -> str:
        """Реальный запрос к Yandex GPT"""
        import requests
        
        messages = []
        if context:
            messages.append({
                "role": "system",
                "text": f"Ты - полезный ассистент. Используй контекст: {context}"
            })
        messages.append({
            "role": "user",
            "text": prompt
        })
        
        payload = {
            "model": self.model,
            "folder_id": self.folder_id,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            f"{self.base_url}/chat",
            json=payload,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return result.get("result", {}).get("message", {}).get("text", "Не удалось сгенерировать ответ.")
        else:
            logger.error(f"Ошибка Yandex API: {response.status_code}")
            return self._get_stub_response(prompt)
    
    def _get_stub_response(self, prompt: str) -> str:
        """Заглушка для ответов"""
        
        # Базовые ответы для разных типов вопросов
        prompt_lower = prompt.lower()
        
        if "привет" in prompt_lower or "здравствуй" in prompt_lower:
            return "👋 Привет! Я чат-бот (работаю в режиме заглушки). Задавайте вопросы, и я постараюсь помочь!"
        
        elif "как дела" in prompt_lower:
            return "😊 У меня всё отлично! Спасибо, что спросили. А как ваши дела?"
        
        elif "кто ты" in prompt_lower or "ты кто" in prompt_lower:
            return "🤖 Я чат-бот на основе Yandex GPT. Сейчас я работаю в режиме заглушки, так как API ключи не настроены."
        
        elif "помощь" in prompt_lower or "help" in prompt_lower:
            return "📚 Я могу:\n- Отвечать на ваши вопросы\n- Помнить историю диалога\n- Искать в базе знаний (/knowledge)\n\nПопробуйте задать мне любой вопрос!"
        
        elif "погода" in prompt_lower:
            return "🌤️ Извините, я не могу узнать погоду в режиме заглушки. Но вы можете использовать Яндекс Погоду!"
        
        elif "время" in prompt_lower:
            from datetime import datetime
            now = datetime.now().strftime("%H:%M:%S")
            return f"🕐 Текущее время: {now}"
        
        elif "спасибо" in prompt_lower:
            return "🙏 Пожалуйста! Всегда рад помочь. Если есть вопросы - обращайтесь."
        
        else:
            return (
                f"📝 Вы спросили: \"{prompt}\"\n\n"
                "Извините, я сейчас работаю в режиме заглушки, так как API ключи Yandex не настроены.\n\n"
                "Чтобы включить полноценную работу, добавьте в .env:\n"
                "YANDEX_API_KEY=ваш_ключ\n"
                "YANDEX_FOLDER_ID=ваш_folder_id\n\n"
                "Доступные команды:\n"
                "/start - Приветствие\n"
                "/help - Помощь\n"
                "/history - История сообщений\n"
                "/knowledge - Поиск в базе знаний"
            )
    
    def search_knowledge_base(self, db, query: str) -> Optional[str]:
        """Поиск в базе знаний"""
        try:
            from app.database import get_knowledge
            results = get_knowledge(db, query)
            if results:
                context = "\n\n".join([f"#{i+1} {r.title}:\n{r.content}" for i, r in enumerate(results[:3])])
                return f"📚 Найдена информация:\n\n{context}"
            return None
        except Exception as e:
            logger.error(f"Ошибка поиска в базе знаний: {e}")
            return None