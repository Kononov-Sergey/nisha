import asyncio
import aiohttp
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import time
from urllib.parse import quote
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from app.services.nlp_service import nlp_service
from app.core.config import settings

class PikabuParser:
    def __init__(self):
        self.tags = ['Бизнес', 'Негатив', 'Стартап']
        self.base_url = "https://pikabu.ru"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        self.driver = None
    
    def _setup_driver(self):
        """Настройка Chrome WebDriver"""
        if self.driver is None:
            chrome_options = Options()
            chrome_options.add_argument('--headless')  # Запуск в фоновом режиме
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument(f'--user-agent={self.headers["User-Agent"]}')
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
        return self.driver
    
    def _close_driver(self):
        """Закрытие WebDriver"""
        if self.driver:
            self.driver.quit()
            self.driver = None

    async def _open_request(self, session: aiohttp.ClientSession, url: str, headers: Dict, params: Optional[Dict] = None):
        """Поддержка как реального aiohttp, так и тестовых AsyncMock.

        Возвращает объект-асинхронный контекстный менеджер ответа.
        """
        request_obj = session.get(url, headers=headers, params=params)
        if asyncio.iscoroutine(request_obj):
            # Для AsyncMock нужно сначала await, чтобы получить объект с __aenter__
            request_obj = await request_obj
        return request_obj
    
    def _scroll_and_collect_urls(
        self,
        url: str,
        max_no_change_scrolls: int = 3,
        max_total_scrolls: int = 50,
        wait_between_scrolls_sec: float = 2.0,
    ) -> List[str]:
        """Скроллим страницу до конца (lazy loading) и собираем ссылки на посты.

        Останавливаемся, когда несколько последовательных скроллов не приводят к росту высоты
        страницы, либо при достижении верхнего лимита скроллов.
        """
        try:
            driver = self._setup_driver()
            driver.get(url)
            
            # Ждем загрузки первоначального контента
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "story__title-link"))
            )
            
            # Собираем URL-ы постов
            collected_urls = set()
            last_height = driver.execute_script("return document.body.scrollHeight")
            no_change_attempts = 0
            total_scrolls = 0
            
            while no_change_attempts < max_no_change_scrolls and total_scrolls < max_total_scrolls:
                # Находим все ссылки на посты на текущей странице
                story_links = driver.find_elements(By.CLASS_NAME, "story__title-link")
                for link in story_links:
                    href = link.get_attribute("href")
                    if href:
                        collected_urls.add(href)
                
                # Скроллим вниз
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                # Ждем загрузки нового контента
                time.sleep(wait_between_scrolls_sec)
                
                # Проверяем, изменилась ли высота страницы (загрузился ли новый контент)
                new_height = driver.execute_script("return document.body.scrollHeight")
                
                if new_height == last_height:
                    # Если высота не изменилась, пробуем еще несколько раз
                    no_change_attempts += 1
                    time.sleep(1)
                else:
                    # Высота изменилась, сбрасываем счетчик
                    no_change_attempts = 0
                    last_height = new_height
                total_scrolls += 1
            
            print(f"Собрано {len(collected_urls)} URL-ов постов")
            return list(collected_urls)
            
        except Exception as e:
            print(f"Ошибка при скроллинге страницы: {e}")
            return []
    
    async def _parse_full_post(self, session: aiohttp.ClientSession, post_url: str) -> Dict:
        """Парсинг полной версии отдельного поста"""
        try:
            cm = await self._open_request(session, post_url, headers=self.headers)
            async with cm as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Извлекаем заголовок
                    title_element = soup.find('h1', class_='story__title')
                    title = title_element.get_text(strip=True) if title_element else ""
                    
                    # Извлекаем полный текст поста
                    content_element = soup.find('div', class_='story__content-inner')
                    if not content_element:
                        return None
                    
                    # Убираем лишние элементы (рекламу, кнопки и т.д.)
                    for unwanted in content_element.find_all(['script', 'style', 'noscript']):
                        unwanted.decompose()
                    
                    text = content_element.get_text(strip=True)
                    if len(text) < 50:  # Слишком короткие посты пропускаем
                        return None
                    
                    # Анализ на боли
                    nlp_result = nlp_service.analyze_text(text)
                    
                    if nlp_result['has_pain']:
                        # Извлекаем автора
                        author_element = soup.find('a', class_='user__nick')
                        author = author_element.get_text(strip=True) if author_element else "Unknown"
                        
                        # Извлекаем ID поста из URL
                        platform_id = post_url.split('/')[-1] if post_url else ""
                        
                        post_data = {
                            'source': 'pikabu',
                            'platform_id': platform_id,
                            'author': author,
                            'text': f"{title}\n\n{text}"[:2000],  # Увеличиваем лимит для полных постов
                            'url': post_url,
                            'pain_keywords': nlp_result['pain_keywords'],
                            'sentiment_score': nlp_result['sentiment_score'],
                            'pain_intensity': nlp_result['pain_intensity'],
                            'has_pain': True,
                        }
                        return post_data
                    
        except Exception as e:
            print(f"Ошибка парсинга поста {post_url}: {e}")
            return None

    async def _get_tag_posts_url(self, session: aiohttp.ClientSession, tag: str) -> List[Dict]:
        """Получение и парсинг постов по тегу с использованием Selenium для lazy loading.

        Тег кодируется в URI-формат (включая кириллицу).
        """
        try:
            encoded_tag = quote(tag.strip(), safe='')
            url = f"{self.base_url}/tag/{encoded_tag}"
            
            # Используем Selenium для получения всех URL-ов с lazy loading
            post_urls = self._scroll_and_collect_urls(url)
            
            # Парсим каждый пост полностью
            posts = []
            for post_url in post_urls:
                post_data = await self._parse_full_post(session, post_url)
                if post_data:
                    posts.append(post_data)
            
            # Закрываем драйвер после использования
            self._close_driver()
            
            return posts

        except Exception as e:
            print(f"Ошибка парсинга Pikabu тега {tag}: {e}")
            self._close_driver()  # Убеждаемся, что драйвер закрыт при ошибке
            return []

    
    async def _parse_page(self, session: aiohttp.ClientSession, page: int) -> List[Dict]:
        """Парсинг одной страницы"""
        try:
            url = f"{self.base_url}/new?page={page}"
            
            cm = await self._open_request(session, url, headers=self.headers)
            async with cm as response:
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
                                    'pain_intensity': nlp_result['pain_intensity'],
                                    'has_pain': True,
                                }
                                posts.append(post_data)
                                
                        except Exception as e:
                            print(f"Ошибка обработки поста: {e}")
                            continue
                    
                    return posts
                    
        except Exception as e:
            print(f"Ошибка парсинга страницы {page}: {e}")
            return []
    
    async def parse_posts_by_tags(self, limit_per_tag: int = 20, tags: Optional[List[str]] = None) -> List[Dict]:
        """Парсинг постов по списку тегов (или self.tags) с использованием Selenium.

        - Теги могут быть кириллическими — кодируются в URI.
        - Для каждой страницы тега скроллим до конца, собираем ссылки и парсим полные посты.
        """
        all_posts = []
        
        async with aiohttp.ClientSession() as session:
            tags_to_process = tags if tags is not None else self.tags
            for tag in tags_to_process:
                print(f"Парсинг тега: {tag}")
                posts = await self._get_tag_posts_url(session, tag)
                
                # Ограничиваем количество постов на тег
                if len(posts) > limit_per_tag:
                    posts = posts[:limit_per_tag]
                
                all_posts.extend(posts)
                print(f"Найдено {len(posts)} постов с болями для тега {tag}")
        
        return all_posts

    async def parse_posts_by_tags_csv(self, tags_csv: str, limit_per_tag: int = 20) -> List[Dict]:
        """Парсинг постов по тегам, переданным через запятую.

        Пример: "Бизнес, Негатив, Стартап".
        """
        if not tags_csv:
            return []
        tags_list = [t.strip() for t in tags_csv.split(',') if t.strip()]
        return await self.parse_posts_by_tags(limit_per_tag=limit_per_tag, tags=tags_list)

    async def parse_recent_posts(self, pages: int = 3) -> List[Dict]:
        """Парсинг недавних постов со страницы /new?page=... для первых N страниц.

        Метод сохранен для обратной совместимости с тестами.
        """
        try:
            results: List[Dict] = []
            async with aiohttp.ClientSession() as session:
                for page in range(1, pages + 1):
                    page_posts = await self._parse_page(session, page)
                    results.extend(page_posts)
                    await asyncio.sleep(settings.PARSING_DELAY)
            return results
        except Exception as e:
            print(f"Ошибка при парсинге недавних постов: {e}")
            return []
