from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # База данных
    DATABASE_URL: str = "sqlite:///./data/pain_detector.db"
    
    # API ключи
    VK_ACCESS_TOKEN: Optional[str] = None
    TELEGRAM_API_ID: Optional[int] = None
    TELEGRAM_API_HASH: Optional[str] = None
    TGSTAT_TOKEN: Optional[str] = None
    
    # NLP настройки
    SPACY_MODEL: str = "ru_core_news_lg"
    PAIN_KEYWORDS: list = [
        "ненавижу", "проблема", "хочу чтобы", "раздражает",
        "неудобно", "сложно", "трудно", "мешает", "бесит"
    ]
    
    # Настройки парсинга
    MAX_POSTS_PER_SOURCE: int = 100
    PARSING_DELAY: float = 1.0  # секунды между запросами
    
    class Config:
        env_file = ".env"

settings = Settings()
