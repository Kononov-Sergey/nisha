from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import Optional

class Settings(BaseSettings):
    # Конфиг загрузки
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

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
    
    @field_validator('TELEGRAM_API_ID', mode='before')
    @classmethod
    def _coerce_telegram_api_id(cls, v):
        if v is None:
            return None
        try:
            v_str = str(v).strip()
            if v_str == '' or v_str.lower() in {'none', 'null'}:
                return None
            return int(v_str)
        except Exception:
            # Игнорируем некорректные значения из .env
            return None

settings = Settings()
