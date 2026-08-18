import os
import sys
import logging
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.telegram_bot import TelegramBot
from app.database import init_db
from app.doc_loader import DocLoader

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Application:
    def __init__(self):
        load_dotenv()
        self.bot = None
        self.max_retries = 3
        self.retry_delay = 5  # секунд
        
    async def start(self):
        """Запуск приложения"""
        try:
            logger.info("🚀 Запуск приложения...")
            
            # Инициализация базы данных
            logger.info("🔄 Инициализация базы данных...")
            init_db()
            logger.info("✅ База данных инициализирована")
            
            # Проверка базы знаний
            logger.info("🔄 Проверка базы знаний...")
            db = None
            try:
                from app.database import SessionLocal
                from app.models import DocFragment
                db = SessionLocal()
                count = db.query(DocFragment).filter(DocFragment.is_active == True).count()
                logger.info(f"📚 В базе знаний {count} активных фрагментов")
                
                if count == 0:
                    logger.warning("⚠️ База знаний пуста! Загружаем демонстрационные данные...")
                    loader = DocLoader()
                    result = loader.update_knowledge_base(update_type="manual")
                    logger.info(f"✅ Результат загрузки: {result}")
            except Exception as e:
                logger.error(f"❌ Ошибка при проверке базы знаний: {e}")
            finally:
                if db:
                    db.close()
            
            # Создаем бота
            self.bot = TelegramBot()
            self.bot.setup_handlers()
            
            # Запускаем с повторными попытками
            for attempt in range(1, self.max_retries + 1):
                try:
                    logger.info(f"🤖 Попытка {attempt}/{self.max_retries} запуска бота...")
                    await self.bot.start_bot()
                    break  # Успешно запустился
                except Exception as e:
                    logger.error(f"❌ Ошибка при запуске бота (попытка {attempt}): {e}")
                    if attempt < self.max_retries:
                        logger.info(f"⏳ Повтор через {self.retry_delay} секунд...")
                        await asyncio.sleep(self.retry_delay)
                    else:
                        raise  # Последняя попытка не удалась
            
            # Держим приложение запущенным
            while True:
                await asyncio.sleep(1)
            
        except KeyboardInterrupt:
            logger.info("👋 Приложение остановлено пользователем")
        except Exception as e:
            logger.error(f"❌ Ошибка: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    async def stop(self):
        """Остановка приложения"""
        logger.info("🛑 Остановка приложения...")
        if self.bot:
            await self.bot.stop_bot()
        logger.info("✅ Приложение остановлено")
    
    def run(self):
        """Запуск приложения в синхронном режиме"""
        try:
            asyncio.run(self.start())
        except KeyboardInterrupt:
            logger.info("👋 Приложение остановлено пользователем")

def main():
    """Точка входа"""
    app = Application()
    app.run()

if __name__ == "__main__":
    main()