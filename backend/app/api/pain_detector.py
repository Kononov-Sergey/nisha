from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
import json
from datetime import datetime, timedelta

from app.core.database import get_db
from app.models.pain_post import PainPost
from app.schemas.pain_post import PainPostResponse, SearchRequest
from app.services.vk_parser import VKParser
from app.services.telegram_parser import TelegramParser 
from app.services.pikabu_parser import PikabuParser

router = APIRouter()

@router.post("/search", response_model=List[PainPostResponse])
async def search_pains(
    request: SearchRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Поиск болей в социальных сетях"""
    
    # Запуск парсинга в фоне
    background_tasks.add_task(parse_all_sources, request.keywords)
    
    # Возвращаем уже имеющиеся результаты
    query = db.query(PainPost)
    
    # Фильтрация по дате
    if request.date_from:
        query = query.filter(PainPost.created_at >= request.date_from)
    if request.date_to:
        query = query.filter(PainPost.created_at <= request.date_to)
    
    # Фильтрация по платформе
    if request.platforms:
        query = query.filter(PainPost.source.in_(request.platforms))
    
    # Сортировка по интенсивности боли
    posts = query.order_by(PainPost.pain_intensity.desc()).limit(50).all()
    
    return posts

@router.get("/results", response_model=List[PainPostResponse])
async def get_results(
    platform: Optional[str] = None,
    min_intensity: Optional[float] = 0.0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Получение результатов поиска"""
    
    query = db.query(PainPost)
    
    if platform:
        query = query.filter(PainPost.source == platform)
    
    query = query.filter(PainPost.pain_intensity >= min_intensity)
    
    posts = query.order_by(PainPost.pain_intensity.desc()).limit(limit).all()
    
    return posts

@router.get("/export")
async def export_top_pains(db: Session = Depends(get_db)):
    """Экспорт топ-5 болей в CSV"""
    
    # Получаем топ-5 болей
    posts = db.query(PainPost)\
              .order_by(PainPost.pain_intensity.desc())\
              .limit(5)\
              .all()
    
    if not posts:
        raise HTTPException(status_code=404, detail="Данные не найдены")
    
    # Формируем CSV
    csv_lines = ["Источник,Автор,Текст,Интенсивность боли,Ключевые слова"]
    
    for post in posts:
        # Экранируем кавычки в тексте
        text = post.text.replace('"', '""')[:100] + "..."
        keywords = ",".join(json.loads(post.pain_keywords))
        
        line = f'"{post.source}","{post.author}","{text}","{post.pain_intensity}","{keywords}"'
        csv_lines.append(line)
    
    csv_content = "\n".join(csv_lines)
    
    return {
        "filename": f"top_pains_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        "content": csv_content
    }

async def parse_all_sources(keywords: List[str]):
    """Фоновая функция парсинга всех источников"""
    
    try:
        # VK парсинг
        vk_parser = VKParser()
        vk_groups = ["typicalkazan", "spb_today", "msk_now"]  # Примеры групп
        vk_posts = await vk_parser.parse_groups(vk_groups)
        save_posts_to_db(vk_posts)
        
    except Exception as e:
        print(f"Ошибка VK парсинга: {e}")
    
    try:
        # Telegram парсинг
        tg_parser = TelegramParser()
        tg_channels = ["businessrussia", "entrepreneurs"]  # Примеры каналов
        tg_posts = await tg_parser.parse_channels(tg_channels)
        save_posts_to_db(tg_posts)
        
    except Exception as e:
        print(f"Ошибка Telegram парсинга: {e}")
    
    try:
        # Pikabu парсинг
        pikabu_parser = PikabuParser()
        pikabu_posts = await pikabu_parser.parse_recent_posts()
        save_posts_to_db(pikabu_posts)
        
    except Exception as e:
        print(f"Ошибка Pikabu парсинга: {e}")

def save_posts_to_db(posts: List[dict]):
    """Сохранение постов в базу данных"""
    from app.core.database import SessionLocal
    
    db = SessionLocal()
    try:
        for post_data in posts:
            # Проверяем, не существует ли уже такой пост
            existing = db.query(PainPost).filter(
                PainPost.source == post_data['source'],
                PainPost.platform_id == post_data['platform_id']
            ).first()
            
            if not existing:
                post = PainPost(
                    source=post_data['source'],
                    platform_id=post_data['platform_id'],
                    author=post_data['author'],
                    text=post_data['text'],
                    url=post_data['url'],
                    pain_keywords=json.dumps(post_data['pain_keywords'], ensure_ascii=False),
                    sentiment_score=post_data['sentiment_score'],
                    pain_intensity=post_data['pain_intensity']
                )
                db.add(post)
        
        db.commit()
        print(f"Сохранено {len(posts)} новых постов")
        
    except Exception as e:
        print(f"Ошибка сохранения в БД: {e}")
        db.rollback()
    finally:
        db.close()
