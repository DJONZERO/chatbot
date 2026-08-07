import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator, Optional, List
from dotenv import load_dotenv

load_dotenv()

# Используем PostgreSQL
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "chatbot_db")
DB_USER = os.getenv("DB_USER", "chatbot_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "chatbot_password")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    from app import models
    Base.metadata.create_all(bind=engine)
    print("✅ База данных PostgreSQL инициализирована")

# ============================================
# ФУНКЦИИ ДЛЯ РАБОТЫ С ПОЛЬЗОВАТЕЛЯМИ
# ============================================

def get_user(db: Session, telegram_id: str) -> Optional['User']:
    """Получить пользователя по telegram_id"""
    from app.models import User
    return db.query(User).filter(User.telegram_id == str(telegram_id)).first()

def create_user(db: Session, telegram_id: str, username: str = None, first_name: str = None, last_name: str = None) -> 'User':
    """Создать нового пользователя"""
    from app.models import User
    user = User(
        telegram_id=str(telegram_id),
        username=username,
        first_name=first_name,
        last_name=last_name
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def get_or_create_user(db: Session, telegram_id: str, username: str = None, first_name: str = None, last_name: str = None) -> 'User':
    """Получить пользователя или создать нового"""
    user = get_user(db, telegram_id)
    if not user:
        user = create_user(db, telegram_id, username, first_name, last_name)
    return user

# ============================================
# ФУНКЦИИ ДЛЯ РАБОТЫ С СООБЩЕНИЯМИ
# ============================================

def save_message(db: Session, user_id: int, content: str, message_type: str = "user", context_data: str = None) -> 'Message':
    """Сохранить сообщение"""
    from app.models import Message
    message = Message(
        user_id=user_id,
        content=content,
        message_type=message_type,
        context_data=context_data
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message

def get_messages(db: Session, user_id: int, limit: int = 10) -> List['Message']:
    """Получить историю сообщений пользователя"""
    from app.models import Message
    messages = db.query(Message).filter(Message.user_id == user_id).order_by(Message.created_at.desc()).limit(limit).all()
    return messages[::-1]

def get_all_messages(db: Session, user_id: int) -> List['Message']:
    """Получить все сообщения пользователя"""
    from app.models import Message
    return db.query(Message).filter(Message.user_id == user_id).order_by(Message.created_at.asc()).all()

# ============================================
# ФУНКЦИИ ДЛЯ РАБОТЫ С БАЗОЙ ЗНАНИЙ
# ============================================

def save_knowledge(db: Session, title: str, content: str, category: str = None, tags: str = None) -> 'Knowledge':
    """Сохранить запись в базу знаний"""
    from app.models import Knowledge
    knowledge = Knowledge(
        title=title,
        content=content,
        category=category,
        tags=tags
    )
    db.add(knowledge)
    db.commit()
    db.refresh(knowledge)
    return knowledge

def get_knowledge(db: Session, query: str = None) -> List['Knowledge']:
    """Поиск в базе знаний"""
    from app.models import Knowledge
    if query:
        return db.query(Knowledge).filter(
            Knowledge.content.ilike(f"%{query}%") | Knowledge.title.ilike(f"%{query}%")
        ).filter(Knowledge.is_active == True).all()
    return db.query(Knowledge).filter(Knowledge.is_active == True).all()

def get_all_knowledge(db: Session) -> List['Knowledge']:
    """Получить все записи из базы знаний"""
    from app.models import Knowledge
    return db.query(Knowledge).filter(Knowledge.is_active == True).all()

def delete_knowledge(db: Session, knowledge_id: int) -> bool:
    """Удалить запись из базы знаний"""
    from app.models import Knowledge
    knowledge = db.query(Knowledge).filter(Knowledge.id == knowledge_id).first()
    if knowledge:
        knowledge.is_active = False
        db.commit()
        return True
    return False

# ============================================
# ФУНКЦИИ ДЛЯ РАБОТЫ С СЕССИЯМИ
# ============================================

def create_session(db: Session, user_id: int, session_id: str, context: str = None) -> 'Session':
    """Создать новую сессию"""
    from app.models import Session
    session = Session(
        user_id=user_id,
        session_id=session_id,
        context=context
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session

def get_session(db: Session, session_id: str) -> Optional['Session']:
    """Получить сессию по ID"""
    from app.models import Session
    return db.query(Session).filter(Session.session_id == session_id, Session.is_active == True).first()

def update_session_context(db: Session, session_id: str, context: str) -> Optional['Session']:
    """Обновить контекст сессии"""
    from app.models import Session
    session = get_session(db, session_id)
    if session:
        session.context = context
        db.commit()
        db.refresh(session)
    return session

# ============================================
# ФУНКЦИИ ДЛЯ ЛОГИРОВАНИЯ
# ============================================

def log_event(db: Session, level: str, module: str, message: str, user_id: int = None) -> 'Log':
    """Логирование события"""
    from app.models import Log
    log = Log(
        level=level,
        module=module,
        message=message,
        user_id=user_id
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log

def get_logs(db: Session, limit: int = 100) -> List['Log']:
    """Получить логи"""
    from app.models import Log
    return db.query(Log).order_by(Log.created_at.desc()).limit(limit).all()