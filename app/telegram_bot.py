import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from telegram.request import HTTPXRequest
from dotenv import load_dotenv

from app.database import get_db, get_or_create_user, save_message, get_messages
from app.yandex_assistant import YandexAssistant
from app.max_integration import MAXIntegration

load_dotenv()

logger = logging.getLogger(__name__)

class TelegramBot:
    def __init__(self):
        self.token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not self.token:
            raise ValueError("TELEGRAM_BOT_TOKEN не установлен!")
        
        self.yandex = YandexAssistant()
        self.max = MAXIntegration()
        self.application = None
    
    def setup_handlers(self) -> None:
        """Настройка обработчиков команд"""
        self.application = Application.builder().token(self.token).connect_timeout(60).read_timeout(60).build()
        
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("help", self.help))
        self.application.add_handler(CommandHandler("history", self.history))
        self.application.add_handler(CommandHandler("knowledge", self.knowledge_search))
        self.application.add_handler(CommandHandler("max_status", self.max_status))
        self.application.add_handler(CommandHandler("update_knowledge", self.update_knowledge))
        
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user = update.effective_user
        db = next(get_db())
        db_user = get_or_create_user(db, user.id, user.username, user.first_name, user.last_name)
        
        max_status = self.max.get_status()
        max_info = "✅ Доступен" if max_status["available"] else "⚠️ Недоступен (заглушка)"
        
        welcome_text = (
            f"👋 Привет, {user.first_name or 'User'}!\n\n"
            "Я — помощник по API hh.ru.\n\n"
            f"📡 MAX: {max_info}\n\n"
            "📚 Доступные команды:\n"
            "/start - Приветствие\n"
            "/help - Помощь\n"
            "/history - История сообщений\n"
            "/knowledge - Поиск в базе знаний\n"
            "/max_status - Статус MAX интеграции\n"
            "/update_knowledge - Обновить базу знаний"
        )
        await update.message.reply_text(welcome_text)
        save_message(db, db_user.id, "/start", "user")
    
    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        help_text = (
            "ℹ️ Помощь:\n\n"
            "/start - Приветствие\n"
            "/help - Эта справка\n"
            "/history - История сообщений\n"
            "/knowledge - Поиск в базе знаний\n"
            "/max_status - Статус MAX интеграции\n"
            "/update_knowledge - Обновить базу знаний\n\n"
            "💬 Просто напишите сообщение, и я отвечу!"
        )
        await update.message.reply_text(help_text)
    
    async def max_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        status = self.max.get_status()
        status_text = (
            "📡 **Статус MAX интеграции**\n\n"
            f"🟢 Доступность: {'✅ Да' if status['available'] else '❌ Нет (заглушка)'}\n"
            f"🔗 API URL: {status['api_url']}\n"
            f"🔑 API KEY: {status['api_key']}\n"
            f"📋 Режим: {status['mode']}"
        )
        await update.message.reply_text(status_text)
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user = update.effective_user
        message_text = update.message.text
        
        if message_text.startswith('/'):
            return
        
        db = next(get_db())
        db_user = get_or_create_user(db, user.id, user.username, user.first_name, user.last_name)
        save_message(db, db_user.id, message_text, "user")
        await update.message.chat.send_action(action="typing")
        
        try:
            response = self.yandex.generate_response(message_text)
            save_message(db, db_user.id, response, "assistant")
            await update.message.reply_text(response)
        except Exception as e:
            logger.error(f"Ошибка при обработке сообщения: {e}")
            await update.message.reply_text("Извините, произошла ошибка. Попробуйте позже.")
    
    async def history(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user = update.effective_user
        db = next(get_db())
        db_user = get_or_create_user(db, user.id)
        messages = get_messages(db, db_user.id, limit=10)
        
        if not messages:
            await update.message.reply_text("📭 История пуста.")
            return
        
        history_text = "📜 Последние сообщения:\n\n"
        for msg in messages:
            role = "👤 Вы" if msg.message_type == "user" else "🤖 Бот"
            history_text += f"{role}: {msg.content[:100]}{'...' if len(msg.content) > 100 else ''}\n\n"
        await update.message.reply_text(history_text)
    
    async def knowledge_search(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if context.args:
            query = " ".join(context.args)
            db = next(get_db())
            result = self.yandex.retriever.search(db, query)
            if result:
                text = "🔍 Найдено:\n\n"
                for i, f in enumerate(result[:3], 1):
                    text += f"[{i}] {f['title']}\n{f['content'][:200]}...\n\n"
                await update.message.reply_text(text)
            else:
                await update.message.reply_text("🔍 Ничего не найдено.")
        else:
            await update.message.reply_text("🔍 /knowledge <запрос>\nПример: /knowledge вакансии")
    
    async def update_knowledge(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user = update.effective_user
        admin_ids = os.getenv("ADMIN_TELEGRAM_IDS", "").split(",")
        if str(user.id) not in admin_ids:
            await update.message.reply_text("⛔ У вас нет прав для выполнения этой команды.")
            return
        
        await update.message.reply_text("🔄 Начинаю обновление базы знаний...")
        
        try:
            from app.doc_loader import DocLoader
            doc_loader = DocLoader()
            result = doc_loader.update_knowledge_base(update_type="manual")
            
            if result["status"] == "success":
                await update.message.reply_text(
                    f"✅ База знаний обновлена!\n\n"
                    f"📊 Результаты:\n"
                    f"- Добавлено: {result['added']} фрагментов\n"
                    f"- Обновлено: {result['updated']} фрагментов\n"
                    f"- Деактивировано: {result['deactivated']} фрагментов\n"
                    f"- Всего активных: {result['total']}"
                )
            else:
                await update.message.reply_text(f"❌ Ошибка обновления: {result.get('error', 'Неизвестная ошибка')}")
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка: {str(e)}")
    
    async def start_bot(self) -> None:
        """Запуск бота"""
        if not self.application:
            self.setup_handlers()
        
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()
        logger.info("🤖 Telegram бот запущен!")
    
    async def stop_bot(self) -> None:
        """Остановка бота"""
        if self.application:
            try:
                if self.application.updater and self.application.updater.running:
                    await self.application.updater.stop()
                    logger.info("🔄 Обновления остановлены")
                
                await self.application.stop()
                logger.info("🤖 Бот остановлен")
            except Exception as e:
                logger.error(f"Ошибка при остановке бота: {e}")
        else:
            logger.warning("⚠️ Бот не был запущен")