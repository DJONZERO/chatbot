import os
import logging
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.models import DocFragment
from pgvector.sqlalchemy import Vector
from app.doc_loader import create_embedding

logger = logging.getLogger(__name__)

class Retriever:
    def __init__(self):
        self.similarity_threshold = float(os.getenv("SIMILARITY_THRESHOLD", "0.5"))
        self.max_fragments = int(os.getenv("MAX_RAG_FRAGMENTS", "5"))
    
    def search(self, db: Session, query: str) -> List[Dict[str, Any]]:
        """Поиск через pgvector (косинусное расстояние)"""
        query_embedding = create_embedding(query)
        if not query_embedding:
            return []
        
        try:
            # Поиск через pgvector
            results = db.query(DocFragment).filter(
                DocFragment.is_active == True,
                DocFragment.embedding.isnot(None)
            ).order_by(
                DocFragment.embedding.op('<->')(query_embedding)
            ).limit(self.max_fragments).all()
            
            fragments = []
            for r in results:
                fragments.append({
                    "id": r.id,
                    "title": r.title,
                    "content": r.content,
                    "endpoint": r.endpoint,
                    "http_method": r.http_method,
                    "source_url": r.source_url,
                    "similarity": 1.0
                })
            
            return fragments
            
        except Exception as e:
            logger.error(f"Ошибка pgvector: {e}")
            return []
    
    def build_context(self, fragments: List[Dict[str, Any]]) -> str:
        """Формирует контекст из найденных фрагментов"""
        if not fragments:
            return None
        
        context = "Вот информация из документации:\n\n"
        for i, f in enumerate(fragments, 1):
            context += f"[{i}] {f['title']}\n{f['content'][:500]}\n"
            if f.get("source_url"):
                context += f"Источник: {f['source_url']}\n"
            context += "\n"
        
        return context