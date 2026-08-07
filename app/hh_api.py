import re
import json
from typing import Dict, Any, Optional, List, Tuple

class HHApiAssistant:
    def __init__(self):
        self.knowledge_base = self._load_knowledge_base()
        self._build_semantic_index()
    
    def _load_knowledge_base(self) -> Dict[str, Dict[str, Any]]:
        """Загружает базу знаний по API hh.ru"""
        return {
            "авторизация": {
                "keywords": ["авторизация", "токен", "access_token", "oauth", "получение токена"],
                "variants": [
                    "как получить токен",
                    "как авторизоваться",
                    "как войти в api",
                    "как получить доступ",
                    "как настроить авторизацию"
                ],
                "answer": "=== АВТОРИЗАЦИЯ В API HH.RU ===\n\nAPI hh.ru использует OAuth 2.0..."
            },
            "поиск вакансий": {
                "keywords": ["поиск", "вакансии", "вакансия", "найти работу", "jobs", "vacancies"],
                "variants": [
                    "как найти работу",
                    "как искать вакансии",
                    "поиск работы в москве",
                    "найти python разработчика",
                    "как найти удаленную работу"
                ],
                "answer": "=== ПОИСК ВАКАНСИЙ В API HH.RU ===\n\nБазовый запрос..."
            },
            "резюме": {
                "keywords": ["резюме", "создать резюме", "обновить резюме", "resume"],
                "variants": [
                    "как создать резюме",
                    "как добавить резюме",
                    "как обновить резюме",
                    "как загрузить резюме"
                ],
                "answer": "=== РАБОТА С РЕЗЮМЕ В API HH.RU ===\n\nСоздание резюме..."
            },
            "отклики": {
                "keywords": ["отклик", "отклики", "откликнуться", "откликнулся"],
                "variants": [
                    "как откликнуться на вакансию",
                    "как отправить отклик",
                    "как ответить на предложение"
                ],
                "answer": "=== РАБОТА С ОТКЛИКАМИ В API HH.RU ===\n\nОтклик на вакансию..."
            },
            "регионы": {
                "keywords": ["регион", "город", "area", "список регионов"],
                "variants": [
                    "как получить список городов",
                    "как найти регион",
                    "какие есть регионы"
                ],
                "answer": "=== СПИСОК РЕГИОНОВ В API HH.RU ===\n\nПолучение списка регионов..."
            },
            "справочники": {
                "keywords": ["справочник", "специализации", "industry", "профессии"],
                "variants": [
                    "какие есть специализации",
                    "как получить отрасли",
                    "список профессий"
                ],
                "answer": "=== СПРАВОЧНИКИ API HH.RU ===\n\nСписок профессиональных областей..."
            }
        }
    
    def _build_semantic_index(self):
        """Строит индекс для семантического поиска"""
        self.semantic_index = {}
        for section, data in self.knowledge_base.items():
            # Добавляем все варианты запросов
            for variant in data.get("variants", []):
                self.semantic_index[variant.lower()] = section
            # Добавляем все ключевые слова
            for keyword in data.get("keywords", []):
                self.semantic_index[keyword.lower()] = section
    
    def _calculate_similarity(self, query: str, candidate: str) -> float:
        """Вычисляет схожесть между запросом и кандидатом"""
        query_words = set(query.lower().split())
        candidate_words = set(candidate.lower().split())
        
        if not query_words or not candidate_words:
            return 0.0
        
        # Количество общих слов
        common = query_words.intersection(candidate_words)
        
        # Коэффициент схожести
        return len(common) / max(len(query_words), len(candidate_words))
    
    def _semantic_search(self, query: str) -> Optional[str]:
        """Семантический поиск по базе знаний"""
        query_lower = query.lower()
        best_match = None
        best_score = 0.0
        
        # Перебираем все варианты из семантического индекса
        for variant, section in self.semantic_index.items():
            score = self._calculate_similarity(query_lower, variant)
            if score > best_score:
                best_score = score
                best_match = section
        
        # Если совпадение достаточно высокое (более 30%)
        if best_score > 0.3:
            return best_match
        
        return None
    
    def find_answer(self, query: str) -> Optional[str]:
        """Поиск ответа в базе знаний (расширенный)"""
        query_lower = query.lower()
        
        # 1. Сначала ищем по ключевым словам (быстрый поиск)
        for section, data in self.knowledge_base.items():
            for keyword in data["keywords"]:
                if keyword.lower() in query_lower:
                    return data["answer"]
        
        # 2. Если не найдено — семантический поиск
        semantic_match = self._semantic_search(query_lower)
        if semantic_match:
            return self.knowledge_base[semantic_match]["answer"]
        
        # 3. Поиск по частичному совпадению (для длинных запросов)
        if len(query_lower.split()) > 3:
            for section, data in self.knowledge_base.items():
                answer_preview = data["answer"].lower()[:100]
                if any(word in answer_preview for word in query_lower.split()[:5]):
                    return data["answer"]
        
        return None
    
    def get_context(self, query: str) -> Optional[str]:
        """Получает контекст для Yandex GPT"""
        answer = self.find_answer(query)
        if answer:
            return f"Найдена информация из базы знаний:\n\n{answer}"
        return None
    
    def get_general_help(self) -> str:
        """Общая справка по API hh.ru"""
        return "=== ПОМОЩНИК ПО API HH.RU ===\n\n" \
               "Я могу помочь с вопросами по API hh.ru. Вот что я знаю:\n\n" \
               "- Авторизация - как получить токен\n" \
               "- Поиск вакансий - как искать вакансии\n" \
               "- Резюме - создание и управление резюме\n" \
               "- Отклики - отклик на вакансии\n" \
               "- Регионы - список регионов\n" \
               "- Справочники - список отраслей и специализаций\n\n" \
               "Просто задайте вопрос в свободной форме!"