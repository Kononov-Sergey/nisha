import spacy
import re
from typing import List, Dict, Tuple
from app.core.config import settings

class NLPService:
    def __init__(self):
        # Загрузка русской модели SpaCy
        try:
            self.nlp = spacy.load(settings.SPACY_MODEL)
        except OSError:
            print(f"Модель {settings.SPACY_MODEL} не найдена. Установите её:")
            print(f"python -m spacy download {settings.SPACY_MODEL}")
            raise
        
        # Паттерны "болей"
        self.pain_patterns = {
            "negative_emotions": [
                r"\b(ненавижу|бесит|раздражает|достал|надоел)\b",
                r"\b(злит|злость|ярость|гнев)\b"
            ],
            "problems": [
                r"\b(проблема|трудность|сложность|затруднение)\w*\b",
                r"\b(не могу|не получается|не выходит)\b"
            ],
            "desires": [
                r"\b(хочу чтобы|хотелось бы|было бы хорошо)\b",
                r"\b(нужно чтобы|необходимо чтобы)\b"
            ],
            "inconvenience": [
                r"\b(неудобно|некомфортно|мешает)\b",
                r"\b(отнимает время|тратится время)\b"
            ]
        }
    
    def analyze_text(self, text: str) -> Dict:
        """Анализ текста на наличие болей и тональность"""
        doc = self.nlp(text)
        
        # Поиск болевых паттернов
        pain_keywords = self._find_pain_keywords(text)
        pain_intensity = self._calculate_pain_intensity(pain_keywords, text)
        
        # Анализ тональности (базовый)
        sentiment_score = self._analyze_sentiment(doc)
        
        # Извлечение ключевых сущностей
        entities = [(ent.text, ent.label_) for ent in doc.ents]
        
        return {
            "pain_keywords": pain_keywords,
            "pain_intensity": pain_intensity,
            "sentiment_score": sentiment_score,
            "entities": entities,
            "has_pain": len(pain_keywords) > 0 and pain_intensity > 0.3
        }
    
    def _find_pain_keywords(self, text: str) -> List[str]:
        """Поиск ключевых слов болей в тексте"""
        found_keywords = []
        text_lower = text.lower()
        
        # Поиск по паттернам
        for category, patterns in self.pain_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, text_lower)
                found_keywords.extend(matches)
        
        # Поиск по прямым ключевым словам
        for keyword in settings.PAIN_KEYWORDS:
            if keyword.lower() in text_lower:
                found_keywords.append(keyword)
        
        return list(set(found_keywords))  # Убираем дубликаты
    
    def _calculate_pain_intensity(self, keywords: List[str], text: str) -> float:
        """Расчет интенсивности боли (0-1)"""
        if not keywords:
            return 0.0
        
        # Базовая интенсивность на основе количества ключевых слов
        base_intensity = min(len(keywords) * 0.2, 1.0)
        
        # Усиливающие факторы
        intensifiers = ["очень", "крайне", "невыносимо", "ужасно", "кошмар"]
        intensifier_boost = sum(1 for word in intensifiers if word in text.lower()) * 0.1
        
        # Восклицательные знаки
        exclamation_boost = min(text.count("!") * 0.05, 0.2)
        
        final_intensity = min(base_intensity + intensifier_boost + exclamation_boost, 1.0)
        return round(final_intensity, 2)
    
    def _analyze_sentiment(self, doc) -> float:
        """Базовый анализ тональности (-1 до 1)"""
        # Простейший метод на основе ключевых слов
        negative_words = ["плохо", "ужасно", "кошмар", "отвратительно", "ненавижу"]
        positive_words = ["хорошо", "отлично", "прекрасно", "замечательно", "люблю"]
        
        text_lower = doc.text.lower()
        
        negative_count = sum(1 for word in negative_words if word in text_lower)
        positive_count = sum(1 for word in positive_words if word in text_lower)
        
        if negative_count + positive_count == 0:
            return 0.0
        
        sentiment = (positive_count - negative_count) / (positive_count + negative_count)
        return round(sentiment, 2)

# Создание единого экземпляра для использования в приложении
nlp_service = NLPService()
