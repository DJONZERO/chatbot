import os
import logging
import requests
from typing import Optional
from dotenv import load_dotenv
from app.hh_api import HHApiAssistant

load_dotenv()

logger = logging.getLogger(__name__)

class YandexAssistant:
    def __init__(self):
        self.api_key = os.getenv("YANDEX_API_KEY")
        self.folder_id = os.getenv("YANDEX_FOLDER_ID")
        self.model = os.getenv("YANDEX_MODEL", "yandexgpt-lite")
        self.use_yandex = False
        self.hh_assistant = HHApiAssistant()

        if self.api_key and self.folder_id:
            self.use_yandex = True
            logger.info("✅ Yandex Assistant инициализирован (режим API)")
            print(f"✅ Yandex GPT включён. API_KEY: {self.api_key[:10]}... FOLDER_ID: {self.folder_id}")
        else:
            logger.warning("⚠️ Yandex Assistant работает в режиме заглушки")
            print("⚠️ Режим заглушки: не найден API_KEY или FOLDER_ID")

    def generate_response(self, prompt: str, context: Optional[str] = None) -> str:
        """Генерация ответа с приоритетом YandexGPT"""
        
        # 1. Сначала пробуем YandexGPT
        if self.use_yandex:
            try:
                response = self._generate_with_yandex(prompt, context)
                # Если YandexGPT вернул осмысленный ответ — возвращаем его
                if response and not response.startswith("⚠️"):
                    return response
            except Exception as e:
                logger.error(f"Ошибка Yandex API: {e}")
        
        # 2. Если YandexGPT не ответил — ищем в базе знаний
        hh_answer = self.hh_assistant.find_answer(prompt)
        if hh_answer:
            return hh_answer
        
        # 3. Если ничего не найдено — заглушка
        return self._get_stub_response(prompt)

    def _generate_with_yandex(self, prompt: str, context: Optional[str] = None) -> str:
        url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
        headers = {
            "Authorization": f"Api-Key {self.api_key}",
            "Content-Type": "application/json"
        }

        messages = [
            {"role": "system", "text": "Ты — профессиональный помощник по API hh.ru. Отвечай понятно и полезно для обычного пользователя. Если вопрос не по теме hh.ru — вежливо скажи об этом."}
        ]
        if context:
            messages.append({"role": "system", "text": f"Контекст из истории: {context}"})
        messages.append({"role": "user", "text": prompt})

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
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                alternatives = result.get('result', {}).get('alternatives', [])
                if alternatives:
                    return alternatives[0].get('message', {}).get('text', 'Не удалось получить ответ.')
                return "Не удалось получить ответ от Yandex GPT."
            else:
                logger.error(f"Ошибка Yandex API: {response.status_code} - {response.text}")
                return f"⚠️ Ошибка YandexGPT: статус {response.status_code}"
        except Exception as e:
            logger.error(f"Ошибка при запросе к Yandex API: {e}")
            return f"⚠️ Ошибка подключения к YandexGPT: {str(e)}"

    def _get_stub_response(self, prompt: str) -> str:
        return "🤖 Я — помощник по API hh.ru. Задайте мне вопрос, например: Как авторизоваться?"

    def search_knowledge_base(self, db, query: str):
        hh_answer = self.hh_assistant.find_answer(query)
        if hh_answer:
            return hh_answer
        return None