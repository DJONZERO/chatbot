from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
from pgvector.sqlalchemy import Vector

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(String(50), unique=True, nullable=False, index=True)
    username = Column(String(100), nullable=True)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    language_code = Column(String(10), default="ru")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    messages = relationship("Message", back_populates="user")
    sessions = relationship("Session", back_populates="user")

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    message_type = Column(String(20), default="user")
    content = Column(Text, nullable=False)
    context_data = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    
    user = relationship("User", back_populates="messages")

class Session(Base):
    __tablename__ = "sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_id = Column(String(100), unique=True, nullable=False, index=True)
    context = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    expires_at = Column(DateTime, nullable=True)
    
    user = relationship("User", back_populates="sessions")

class Knowledge(Base):
    __tablename__ = "knowledge"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    category = Column(String(100), nullable=True)
    tags = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

class Log(Base):
    __tablename__ = "logs"
    
    id = Column(Integer, primary_key=True, index=True)
    level = Column(String(20), nullable=False)
    module = Column(String(50), nullable=False)
    message = Column(Text, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

class KnowledgeUpdateLog(Base):
    __tablename__ = "knowledge_update_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    update_type = Column(String(20), nullable=False)
    status = Column(String(20), nullable=False)
    fragments_added = Column(Integer, default=0)
    fragments_updated = Column(Integer, default=0)
    fragments_deactivated = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime, nullable=True)

class DocFragment(Base):
    __tablename__ = "doc_fragments"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    endpoint = Column(String(255), nullable=True)
    http_method = Column(String(10), nullable=True)
    source_url = Column(String(500), nullable=True)
    section_path = Column(String(500), nullable=True)
    embedding = Column(Vector(384), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    def __repr__(self):
        return f"<DocFragment(id={self.id}, title={self.title})>"