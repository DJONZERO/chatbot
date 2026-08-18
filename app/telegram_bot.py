import os
import logging
import re
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

from app.yandex_assistant import YandexAssistant
from app.database import SessionLocal
from app.models import User, Message

load_dotenv()

logger = logging.getLogger(__name__)

class TelegramBot:
    def __init__(self):
        self.token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not self.token:
            raise ValueError("TELEGRAM_BOT_TOKEN не установлен!")
        
        self.yandex = YandexAssistant()
        self.application = None
        self.admin_ids = [int(id.strip()) for id in os.getenv("ADMIN_TELEGRAM_IDS", "").split(",") if id.strip()]
        logger.info(f"✅ TelegramBot инициализирован")
    
    def setup_handlers(self) -> None:
        """Настройка обработчиков команд"""
        self.application = Application.builder().token(self.token).build()
        
        # Регистрируем команды
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("help", self.help))
        self.application.add_handler(CommandHandler("history", self.history))
        self.application.add_handler(CommandHandler("knowledge", self.knowledge_search))
        self.application.add_handler(CommandHandler("stats", self.stats))
        
        # Обработчик текстовых сообщений
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        logger.info("✅ Обработчики зарегистрированы")
    
    def get_or_create_user(self, db, telegram_id: int, username: str = None, first_name: str = None, last_name: str = None) -> User:
        """Получает или создает пользователя в БД"""
        user = db.query(User).filter(User.telegram_id == telegram_id).first()
        if not user:
            user = User(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
                last_name=last_name
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            logger.info(f"👤 Создан новый пользователь: {telegram_id}")
        return user
    
    def save_message(self, db, user_id: int, content: str, message_type: str) -> Message:
        """Сохраняет сообщение в БД"""
        msg = Message(
            user_id=user_id,
            content=content,
            message_type=message_type
        )
        db.add(msg)
        db.commit()
        db.refresh(msg)
        return msg
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Приветственное сообщение"""
        user = update.effective_user
        
        db = SessionLocal()
        try:
            db_user = self.get_or_create_user(db, user.id, user.username, user.first_name, user.last_name)
            self.save_message(db, db_user.id, "/start", "user")
        except Exception as e:
            logger.error(f"Ошибка при сохранении пользователя: {e}")
        finally:
            db.close()
        
        welcome_text = (
            f"👋 Привет, {user.first_name or 'User'}!\n\n"
            "Я — помощник по API hh.ru.\n\n"
            "📚 **Доступные команды:**\n"
            "/start - Приветствие\n"
            "/help - Помощь\n"
            "/history - История сообщений\n"
            "/knowledge <запрос> - Поиск в базе знаний\n"
            "/stats - Статистика базы знаний\n\n"
            "💬 Просто напишите сообщение, и я отвечу!"
        )
        await update.message.reply_text(welcome_text, parse_mode='Markdown')
    
    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Справка по командам"""
        help_text = (
            "ℹ️ **Помощь:**\n\n"
            "/start - Приветствие\n"
            "/help - Эта справка\n"
            "/history - История сообщений\n"
            "/knowledge <запрос> - Поиск в базе знаний\n"
            "/stats - Статистика базы знаний\n\n"
            "💬 Просто напишите сообщение, и я отвечу!\n\n"
            "**Примеры вопросов:**\n"
            "- Как найти вакансии?\n"
            "- Как авторизоваться в API?\n"
            "- Как создать резюме?\n"
            "- Как откликнуться на вакансию?"
        )
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработка текстовых сообщений"""
        user = update.effective_user
        message_text = update.message.text
        
        # Игнорируем команды
        if message_text.startswith('/'):
            return
        
        logger.info(f"📩 Получено сообщение от {user.id}: {message_text[:50]}...")
        
        # Сохраняем сообщение пользователя
        db = SessionLocal()
        try:
            db_user = self.get_or_create_user(db, user.id, user.username, user.first_name, user.last_name)
            self.save_message(db, db_user.id, message_text, "user")
        except Exception as e:
            logger.error(f"Ошибка при сохранении сообщения: {e}")
        finally:
            db.close()
        
        try:
            # Показываем, что бот печатает
            await update.message.chat.send_action(action="typing")
        except Exception as e:
            logger.warning(f"Не удалось отправить typing action: {e}")
        
        try:
            # Генерируем ответ
            response = self.yandex.generate_response(message_text)
            logger.info(f"📤 Ответ сгенерирован, длина: {len(response)} символов")
            
            # Сохраняем ответ
            db = SessionLocal()
            try:
                db_user = self.get_or_create_user(db, user.id)
                self.save_message(db, db_user.id, response, "assistant")
            except Exception as e:
                logger.error(f"Ошибка при сохранении ответа: {e}")
            finally:
                db.close()
            
            # Отправляем ответ с обработкой ошибок Markdown
            try:
                await update.message.reply_text(response, parse_mode='Markdown')
            except Exception as e:
                # Если ошибка Markdown, отправляем без форматирования
                logger.warning(f"❌ Ошибка Markdown, отправляем без форматирования: {e}")
                clean_response = re.sub(r'[*_`\[\]()~>#+\-=|{}.!]', '', response)
                await update.message.reply_text(clean_response)
            
        except Exception as e:
            logger.error(f"❌ Ошибка при обработке сообщения: {e}")
            import traceback
            traceback.print_exc()
            await update.message.reply_text(
                "❌ Произошла ошибка при обработке запроса. Попробуйте позже."
            )
    
    async def history(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Показывает историю сообщений"""
        user = update.effective_user
        
        db = SessionLocal()
        try:
            db_user = self.get_or_create_user(db, user.id)
            
            messages = db.query(Message).filter(
                Message.user_id == db_user.id
            ).order_by(Message.created_at.desc()).limit(10).all()
            
            if not messages:
                await update.message.reply_text("📭 История пуста.")
                return
            
            history_text = "📜 **Последние сообщения:**\n\n"
            for msg in reversed(messages):
                role = "👤 Вы" if msg.message_type == "user" else "🤖 Бот"
                content = msg.content[:100] + "..." if len(msg.content) > 100 else msg.content
                history_text += f"{role}: {content}\n\n"
            
            await update.message.reply_text(history_text, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Ошибка при получении истории: {e}")
            await update.message.reply_text("❌ Ошибка при получении истории.")
        finally:
            db.close()
    
    async def knowledge_search(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Поиск в базе знаний"""
        if not context.args:
            await update.message.reply_text(
                "🔍 **Использование:** /knowledge <запрос>\n"
                "Пример: /knowledge вакансии",
                parse_mode='Markdown'
            )
            return
        
        query = " ".join(context.args)
        db = SessionLocal()
        try:
            results = self.yandex.retriever.search(db, query)
            
            if not results:
                await update.message.reply_text(
                    f"🔍 По запросу '{query}' ничего не найдено."
                )
                return
            
            text = f"🔍 **Результаты поиска по запросу:** '{query}'\n\n"
            for i, f in enumerate(results[:5], 1):
                text += f"**{i}. {f['title']}**\n"
                text += f"{f['content'][:200]}...\n"
                if f.get('source_url'):
                    text += f"📖 Источник: {f['source_url']}\n"
                text += "\n"
            
            if len(text) > 4000:
                text = text[:3997] + "..."
            
            await update.message.reply_text(text, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Ошибка при поиске: {e}")
            await update.message.reply_text("❌ Ошибка при поиске.")
        finally:
            db.close()
    
    async def stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Статистика базы знаний"""
        db = SessionLocal()
        try:
            from app.models import DocFragment
            count = db.query(DocFragment).filter(DocFragment.is_active == True).count()
            
            stats_text = (
                f"📊 **Статистика базы знаний:**\n\n"
                f"• Всего фрагментов: {count}\n"
                f"• Источник: OpenAPI hh.ru\n"
                f"📖 Документация: https://api.hh.ru/openapi/redoc"
            )
            await update.message.reply_text(stats_text, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Ошибка при получении статистики: {e}")
            await update.message.reply_text("❌ Ошибка при получении статистики.")
        finally:
            db.close()
    
    async def start_bot(self) -> None:
        """Запуск бота"""
        if not self.application:
            self.setup_handlers()
        
        try:
            logger.info("🤖 Подключение к Telegram API...")
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling()
            logger.info("🤖 Telegram бот запущен и готов к работе!")
        except Exception as e:
            logger.error(f"❌ Ошибка при запуске бота: {e}")
            raise
    
    async def stop_bot(self) -> None:
        """Остановка бота"""
        if self.application:
            try:
                if self.application.updater and self.application.updater.running:
                    await self.application.updater.stop()
                    logger.info("🔄 Обновления остановлены")
                
                await self.application.stop()
                await self.application.shutdown()
                logger.info("🤖 Бот остановлен")
            except Exception as e:
                logger.error(f"❌ Ошибка при остановке бота: {e}")


# ============ Функция для запуска бота ============
def run_bot():
    """Запускает бота"""
    import asyncio
    
    bot = TelegramBot()
    bot.setup_handlers()
    
    try:
        asyncio.run(bot.start_bot())
        # Держим бота запущенным
        asyncio.get_event_loop().run_forever()
    except KeyboardInterrupt:
        logger.info("👋 Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"❌ Ошибка при запуске бота: {e}")