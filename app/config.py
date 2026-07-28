import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Класс конфигурации приложения"""
    
    # Telegram
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    
    # Yandex Cloud
    YANDEX_API_KEY = os.getenv("YANDEX_API_KEY")
    YANDEX_FOLDER_ID = os.getenv("YANDEX_FOLDER_ID")
    YANDEX_MODEL = os.getenv("YANDEX_MODEL", "general")
    
    # База данных
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME", "chatbot_db")
    DB_USER = os.getenv("DB_USER", "chatbot_user")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "chatbot_password")
    
    # MAX
    MAX_API_URL = os.getenv("MAX_API_URL")
    MAX_API_KEY = os.getenv("MAX_API_KEY")
    
    # Общие
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    @classmethod
    def validate(cls):
        """Проверка обязательных переменных"""
        required = [
            ("TELEGRAM_BOT_TOKEN", cls.TELEGRAM_BOT_TOKEN),
            ("YANDEX_API_KEY", cls.YANDEX_API_KEY),
            ("YANDEX_FOLDER_ID", cls.YANDEX_FOLDER_ID),
        ]
        missing = []
        for name, value in required:
            if not value:
                missing.append(name)
        
        if missing:
            raise ValueError(f"Отсутствуют обязательные переменные в .env: {', '.join(missing)}")
        
        return True