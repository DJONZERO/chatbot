from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, BigInteger
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from app.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(BigInteger, unique=True, index=True, nullable=False)
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    message_type = Column(String(50), nullable=False)  # 'user' or 'assistant'
    created_at = Column(DateTime, server_default=func.now())

class DocFragment(Base):
    __tablename__ = "doc_fragments"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    endpoint = Column(String(255), nullable=True)
    http_method = Column(String(50), nullable=True)
    source_url = Column(String(500), nullable=True)
    section_path = Column(String(500), unique=True, index=True, nullable=False)
    embedding = Column(Vector(384), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

class KnowledgeUpdateLog(Base):
    __tablename__ = "knowledge_update_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    update_type = Column(String(50), nullable=False)
    status = Column(String(50), nullable=False)
    fragments_added = Column(Integer, default=0)
    fragments_updated = Column(Integer, default=0)
    fragments_deactivated = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime, nullable=True)