from sqlalchemy import Column, Integer, String, Text, DateTime, Float
from sqlalchemy.sql import func
from app.core.database import Base

class PainPost(Base):
    __tablename__ = "pain_posts"
    
    id = Column(Integer, primary_key=True, index=True)
    source = Column(String(50), nullable=False)  # vk, telegram, pikabu
    platform_id = Column(String(100))  # ID поста на платформе
    author = Column(String(100))
    text = Column(Text, nullable=False)
    url = Column(String(500))
    pain_keywords = Column(String(500))  # JSON строка найденных ключевых слов
    sentiment_score = Column(Float)  # Оценка тональности
    pain_intensity = Column(Float)  # Интенсивность "боли"
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    parsed_at = Column(DateTime(timezone=True), server_default=func.now())
