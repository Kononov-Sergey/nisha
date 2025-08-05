import asyncio
import aiohttp
from bs4 import BeautifulSoup
from typing import List, Dict
from app.services.nlp_service import nlp_service
from app.core.config import settings

class PikabuParser:
    def __init__(self):
        self.base_url = "https://pikabu.ru"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
    
    async def parse_recent_posts(self) -> List[Dict]:
        """Парсинг свежих постов с Pikabu"""
        all_posts = []
        
        async with aiohttp.ClientSession() as session:
            try:
                # Парсим несколько страниц "свежего"
                for page in range(1, 4):  # Первые 3 страницы
                    posts = await self._parse_page(session, page)
                    all_posts.extend(posts)
                    
                    # Задержка между страницами
                    await asyncio.sleep(settings.PARSING_DELAY)
                    
            except Exception as e:
                print(f"Ошибка парсинга Pikabu: {e}")
        
        return all_posts
    
    async def _parse_page(self, session: aiohttp.ClientSession, page: int) -> List[Dict]:
        """Парсинг одной страницы"""
        try:
            url = f"{self.base_url}/new?page={page}"
            
            async with session.get(url, headers=self.headers) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    posts = []
                    
                    # Ищем блоки с постами
                    post_blocks = soup.find_all('article', class_='story')
                    
                    for block in post_blocks:
                        try:
                            # Извлекаем текст поста
                            text_element = block.find('div', class_='story__content-inner')
                            if not text_element:
                                continue
                            
                            text = text_element.get_text(strip=True)
                            if len(text) < 50:  # Слишком короткие посты пропускаем
                                continue
                            
                            # Анализ на боли
                            nlp_result = nlp_service.analyze_text(text)
                            
                            if nlp_result['has_pain']:
                                # Извлекаем дополнительную информацию
                                title_element = block.find('h1') or block.find('h2')
                                title = title_element.get_text(strip=True) if title_element else ""
                                
                                link_element = block.find('a', class_='story__title-link')
                                post_url = self.base_url + link_element['href'] if link_element else ""
                                
                                author_element = block.find('a', class_='user__nick')
                                author = author_element.get_text(strip=True) if author_element else "Unknown"
                                
                                post_data = {
                                    'source': 'pikabu',
                                    'platform_id': post_url.split('/')[-1] if post_url else "",
                                    'author': author,
                                    'text': f"{title}\n\n{text}"[:1000],  # Ограничиваем длину
                                    'url': post_url,
                                    'pain_keywords': nlp_result['pain_keywords'],
                                    'sentiment_score': nlp_result['sentiment_score'],
                                    'pain_intensity': nlp_result['pain_intensity']
                                }
                                posts.append(post_data)
                                
                        except Exception as e:
                            print(f"Ошибка обработки поста: {e}")
                            continue
                    
                    return posts
                    
        except Exception as e:
            print(f"Ошибка парсинга страницы {page}: {e}")
            return []
