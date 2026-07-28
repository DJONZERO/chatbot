import os
import sys
import logging
import asyncio
import warnings
from pathlib import Path
from datetime import datetime

warnings.filterwarnings("ignore")

sys.path.append(str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from app.database import init_db
from app.telegram_bot import TelegramBot
from app.max_integration import MAXIntegration
from app.yandex_assistant import YandexAssistant

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'bot_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

class ChatBotApp:
    def __init__(self):
        self.telegram_bot = None
        self.max_integration = MAXIntegration()
        self.yandex_assistant = YandexAssistant()
        self.is_running = False
        self._stop_event = asyncio.Event()
    
    def init_database(self):
        try:
            init_db()
            logger.info("✅ База данных инициализирована")
        except Exception as e:
            logger.error(f"❌ Ошибка БД: {e}")
            raise
    
    async def start(self):
        logger.info("🚀 Запуск приложения...")
        self.init_database()
        logger.info(f"📡 MAX: {'✅' if self.max_integration.health_check() else '⚠️ Заглушка'}")
        
        try:
            self.telegram_bot = TelegramBot()
            self.telegram_bot.setup_handlers()
            await self.telegram_bot.start_bot()
            self.is_running = True
            logger.info("✅ Бот запущен! Нажмите Ctrl+C для остановки.")
            
            # Ждем сигнала остановки
            await self._stop_event.wait()
            
        except Exception as e:
            logger.error(f"❌ Ошибка: {e}")
            raise
    
    async def stop(self):
        self.is_running = False
        if self.telegram_bot:
            await self.telegram_bot.stop_bot()
        logger.info("🛑 Приложение остановлено")
    
    def run(self):
        try:
            asyncio.run(self.start())
        except KeyboardInterrupt:
            logger.info("Получен сигнал остановки (Ctrl+C)")
            self._stop_event.set()
            try:
                asyncio.run(self.stop())
            except Exception as e:
                logger.error(f"Ошибка при остановке: {e}")
        except Exception as e:
            logger.error(f"❌ Ошибка: {e}")
            try:
                asyncio.run(self.stop())
            except Exception as e2:
                logger.error(f"Ошибка при остановке: {e2}")
            raise

if __name__ == "__main__":
    print("=" * 60)
    print("🤖 ЧАТ-БОТ С INTEGRATION MAX, YANDEX GPT, TELEGRAM")
    print("=" * 60)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    app = ChatBotApp()
    app.run()
