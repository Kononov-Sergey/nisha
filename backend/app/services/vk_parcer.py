import vk_api
import time
import asyncio
from typing import List, Dict, Optional
from app.core.config import settings
from app.services.nlp_service import nlp_service

class VKParser:
    def __init__(self):
        if not settings.VK_ACCESS_TOKEN:
            raise ValueError("VK_ACCESS_TOKEN не установлен в настройках")
        
        self.vk_session = vk_api.VkApi(token=settings.VK_ACCESS_TOKEN)
        self.vk = self.vk_session.get_api()
    
    async def parse_groups(self, group_domains: List[str]) -> List[Dict]:
        """Парсинг постов из VK групп"""
        all_posts = []
        
        for domain in group_domains:
            try:
                posts = await self._get_group_posts(domain)
                all_posts.extend(posts)
                
                # Задержка между запросами
                await asyncio.sleep(settings.PARSING_DELAY)
                
            except Exception as e:
                print(f"Ошибка парсинга группы {domain}: {e}")
                continue
        
        return all_posts
    
    async def _get_group_posts(self, domain: str) -> List[Dict]:
        """Получение постов группы"""
        try:
            # Получение постов стены группы
            response = self.vk.wall.get(
                domain=domain,
                count=min(settings.MAX_POSTS_PER_SOURCE, 100),
                filter='owner'  # Только посты группы
            )
            
            posts = []
            for post in response['items']:
                # Фильтрация постов с текстом
                if not post.get('text'):
                    continue
                
                # Анализ текста на наличие болей
                nlp_result = nlp_service.analyze_text(post['text'])
                
                if nlp_result['has_pain']:
                    post_data = {
                        'source': 'vk',
                        'platform_id': str(post['id']),
                        'author': domain,
                        'text': post['text'],
                        'url': f"https://vk.com/{domain}?w=wall-{post['owner_id']}_{post['id']}",
                        'pain_keywords': nlp_result['pain_keywords'],
                        'sentiment_score': nlp_result['sentiment_score'],
                        'pain_intensity': nlp_result['pain_intensity'],
                        'has_pain': True,
                    }
                    posts.append(post_data)
            
            return posts
            
        except Exception as e:
            print(f"Ошибка получения постов группы {domain}: {e}")
            return []
