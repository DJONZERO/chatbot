import schedule
import time
import logging
from threading import Thread
from datetime import datetime
from app.doc_loader import DocLoader

logger = logging.getLogger(__name__)

def scheduled_update():
    """Функция для автоматического обновления по расписанию"""
    logger.info("🔄 Запуск планового обновления базы знаний...")
    try:
        loader = DocLoader()
        result = loader.update_knowledge_base(update_type="scheduled")
        logger.info(f"✅ Обновление завершено: добавлено {result.get('added', 0)}, обновлено {result.get('updated', 0)}")
        return result
    except Exception as e:
        logger.error(f"❌ Ошибка при плановом обновлении: {e}")
        return {"status": "failed", "error": str(e)}

def start_scheduler():
    """Запускает планировщик в фоновом потоке"""
    schedule.every().day.at("03:00").do(scheduled_update)
    
    
    def run_scheduler():
        logger.info("🕐 Планировщик запущен. Обновление каждый день в 3:00")
        while True:
            schedule.run_pending()
            time.sleep(60)
    
    thread = Thread(target=run_scheduler, daemon=True)
    thread.start()
    return thread