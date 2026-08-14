import os
import logging
import requests
from typing import Optional
from dotenv import load_dotenv
from app.retriever import Retriever
from app.database import SessionLocal

load_dotenv()

logger = logging.getLogger(__name__)

class YandexAssistant:
    def __init__(self):
        self.api_key = os.getenv("YANDEX_API_KEY")
        self.folder_id = os.getenv("YANDEX_FOLDER_ID")
        self.model = os.getenv("YANDEX_MODEL", "yandexgpt-lite")
        self.use_yandex = False
        self.retriever = Retriever()
        
        if self.api_key and self.folder_id:
            self.use_yandex = True
            logger.info("✅ Yandex Assistant инициализирован (режим API)")
        else:
            logger.warning("⚠️ Yandex Assistant работает в режиме заглушки")
    
    def generate_response(self, prompt: str, context: Optional[str] = None) -> str:
        """Генерирует ответ с использованием Yandex GPT и RAG"""
        
        # 1. Ищем в базе знаний через pgvector
        db = SessionLocal()
        try:
            fragments = self.retriever.search(db, prompt)
            if fragments:
                context = self.retriever.build_context(fragments)
                if context:
                    return self._call_yandex_gpt_with_context(prompt, context)
            else:
                return "К сожалению, в документации API hh.ru не найдена информация по вашему запросу. Попробуйте переформулировать вопрос или обратитесь к официальной документации: https://api.hh.ru/openapi/redoc"
        finally:
            db.close()
        
        # Если Yandex недоступен
        return "Извините, я не могу ответить на этот вопрос."
    
    def _call_yandex_gpt(self, prompt: str) -> str:
        """Вызов Yandex GPT без контекста"""
        messages = [
            {"role": "user", "text": prompt}
        ]
        return self._call_yandex_api(messages)
    
    def _call_yandex_gpt_with_context(self, prompt: str, context: str) -> str:
        """Вызов Yandex GPT с контекстом из базы знаний"""
        messages = [
            {
                "role": "system",
                "text": f"Ты — помощник по API hh.ru. Отвечай на вопросы, используя только информацию из контекста. Если в контексте нет ответа, скажи об этом честно.\n\nКонтекст:\n{context}"
            },
            {
                "role": "user",
                "text": prompt
            }
        ]
        return self._call_yandex_api(messages)
    
    def _call_yandex_api(self, messages: list) -> str:
        """Универсальный вызов Yandex GPT API"""
        url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
        headers = {
            "Authorization": f"Api-Key {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "modelUri": f"gpt://{self.folder_id}/{self.model}",
            "completionOptions": {
                "stream": False,
                "temperature": 0.7,
                "maxTokens": 1000
            },
            "messages": messages
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            
            if response.status_code == 200:
                result = response.json()
                alternatives = result.get('result', {}).get('alternatives', [])
                if alternatives:
                    return alternatives[0].get('message', {}).get('text', 'Не удалось получить ответ.')
                return "Не удалось получить ответ от Yandex GPT."
            else:
                logger.error(f"Ошибка Yandex API: {response.status_code} - {response.text}")
                return "Извините, произошла ошибка при обращении к Yandex GPT."
        except Exception as e:
            logger.error(f"Ошибка при запросе к Yandex GPT: {e}")
            return "Извините, произошла ошибка при обработке запроса."