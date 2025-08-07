import asyncio
import aiohttp
from typing import List, Dict
from app.core.config import settings
from app.services.nlp_service import nlp_service

class TelegramParser:
    def __init__(self):
        if not settings.TGSTAT_TOKEN:
            raise ValueError("TGSTAT_TOKEN не установлен в настройках")
        
        self.base_url = "https://api.tgstat.ru"
        self.headers = {
            "Authorization": f"Bearer {settings.TGSTAT_TOKEN}"
        }
    
    async def parse_channels(self, channel_names: List[str]) -> List[Dict]:
        """Парсинг постов из Telegram каналов через TGStat API"""
        all_posts = []
        
        async with aiohttp.ClientSession() as session:
            for channel in channel_names:
                try:
                    posts = await self._get_channel_posts(session, channel)
                    all_posts.extend(posts)
                    
                    # Задержка между запросами
                    await asyncio.sleep(settings.PARSING_DELAY)
                    
                except Exception as e:
                    print(f"Ошибка парсинга канала {channel}: {e}")
                    continue
        
        return all_posts
    
    async def _get_channel_posts(self, session: aiohttp.ClientSession, channel: str) -> List[Dict]:
        """Получение постов канала через TGStat API"""
        try:
            # Поиск постов по ключевым словам
            pain_keywords_query = " OR ".join(settings.PAIN_KEYWORDS[:5])  # Берем первые 5 ключевых слов
            
            url = f"{self.base_url}/posts/search"
            params = {
                "q": pain_keywords_query,
                "peer_type": "channel",
                "limit": min(settings.MAX_POSTS_PER_SOURCE, 50)
            }
            # Поддержка AsyncMock: session.get может возвращать coroutine
            req = session.get(url, headers=self.headers, params=params)
            if asyncio.iscoroutine(req):
                req = await req
            async with req as response:
                if response.status == 200:
                    data = await response.json()
                    posts = []
                    
                    for post in data.get('response', {}).get('items', []):
                        text = post.get('text', '')
                        if not text:
                            continue
                        
                        # Анализ текста
                        nlp_result = nlp_service.analyze_text(text)
                        
                        if nlp_result['has_pain']:
                            post_data = {
                                'source': 'telegram',
                                'platform_id': str(post.get('id')),
                                'author': post.get('channel', {}).get('title', 'Unknown'),
                                'text': text,
                                'url': post.get('link', ''),
                                'pain_keywords': nlp_result['pain_keywords'],
                                'sentiment_score': nlp_result['sentiment_score'],
                                'pain_intensity': nlp_result['pain_intensity'],
                                'has_pain': True,
                            }
                            posts.append(post_data)
                    
                    return posts
                else:
                    print(f"Ошибка API TGStat: {response.status}")
                    return []
                    
        except Exception as e:
            print(f"Ошибка получения постов канала {channel}: {e}")
            return []
