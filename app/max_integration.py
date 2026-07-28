import os
import logging
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class MAXIntegration:
    def __init__(self):
        self.api_url = os.getenv("MAX_API_URL")
        self.api_key = os.getenv("MAX_API_KEY")
        self.available = False
        self._check_availability()
    
    def _check_availability(self) -> bool:
        if not self.api_url or not self.api_key:
            logger.warning("⚠️ MAX API не настроен")
            self.available = False
            return False
        self.available = True
        return True
    
    def send_message(self, user_id: str, message: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        if not self.available:
            logger.info(f"📝 MAX заглушка: сообщение от {user_id}: {message[:50]}...")
            return {
                "status": "stub",
                "message": "MAX недоступен (заглушка)",
                "user_id": user_id
            }
        return {"status": "error", "message": "MAX не настроен"}
    
    def health_check(self) -> bool:
        return self.available
    
    def get_status(self) -> Dict[str, Any]:
        return {
            "available": self.available,
            "api_url": self.api_url or "не настроен",
            "api_key": "✅ установлен" if self.api_key else "❌ не установлен",
            "mode": "stub" if not self.available else "live"
        }