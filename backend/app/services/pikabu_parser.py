import asyncio
import aiohttp
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import re
import time
from urllib.parse import quote
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.service import Service
import os
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
            chrome_options.add_argument('--headless=new')  # Современный headless режим Chrome
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=320,1080')
            chrome_options.add_argument(f'--user-agent={self.headers["User-Agent"]}')

            # Позволяем указать бинарник Chrome/Chromium через переменную окружения
            chrome_binary = os.environ.get('CHROME_BINARY')
            if chrome_binary and os.path.exists(chrome_binary):
                chrome_options.binary_location = chrome_binary

            # Используем Selenium Manager (встроен в selenium 4.6+) — драйвер подберётся автоматически
            try:
                self.driver = webdriver.Chrome(options=chrome_options)
            except Exception as e:
                print(f"Не удалось инициализировать WebDriver через Selenium Manager: {e}")
                self.driver = None
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
        wait_between_scrolls_sec: float = 1,
    ) -> List[str]:
        """Скроллим страницу до конца (lazy loading) и собираем ссылки на посты.

        Останавливаемся, когда несколько последовательных скроллов не приводят к росту высоты
        страницы, либо при достижении верхнего лимита скроллов, либо когда собрали
        все посты согласно счётчику результатов на странице.
        """
        try:
            driver = self._setup_driver()
            print(f"[Pikabu] Открываю страницу тега: {url}")
            driver.get(url)
            
            # Ждем загрузки первоначального контента
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "story__title-link"))
            )
            
            # Пытаемся считать ожидаемое число результатов (например, "876 постов")
            expected_total_posts = None
            try:
                counter_el = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'span[class*="results-stories__count"]'))
                )
                digits = re.sub(r"\D+", "", (counter_el.text or ""))
                if digits:
                    expected_total_posts = int(digits)
                    print(f"[Pikabu] Ожидаемое количество постов по счётчику: {expected_total_posts}")
            except Exception:
                pass

            # Собираем URL-ы постов
            collected_urls = set()
            last_height = driver.execute_script("return document.body.scrollHeight")
            no_change_attempts = 0
            total_scrolls = 0
            
            while no_change_attempts < max_no_change_scrolls:
                # Находим все ссылки на посты на текущей странице
                story_links = driver.find_elements(By.CLASS_NAME, "story__title-link")
                for link in story_links:
                    href = link.get_attribute("href")
                    if href:
                        collected_urls.add(href)
                print(f"[Pikabu] Собрано ссылок: {len(collected_urls)} после {total_scrolls} скроллов")

                # Если знаем ожидаемое число постов и уже набрали не меньше — выходим
                if expected_total_posts is not None and len(collected_urls) >= expected_total_posts:
                    print(f"[Pikabu] Достигнут счётчик: {len(collected_urls)}/{expected_total_posts}")
                    break
                
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
            self._close_driver()
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
                        # make post_data pretty in console
                        print("-"*100)
                        print(f"Title: {title}")
                        print(f"Author: {author}")
                        print(f"Platform ID: {platform_id}")
                        print(f"Text: {text}")
                        print(f"Pain Keywords: {nlp_result['pain_keywords']}")
                        print(f"Sentiment Score: {nlp_result['sentiment_score']}")
                        print(f"Pain Intensity: {nlp_result['pain_intensity']}")
                        print("-"*100)
                        
                        print(f"[Pikabu] Найден пост с болью: {post_url}")
                        return post_data
                    
        except Exception as e:
            print(f"Ошибка парсинга поста {post_url}: {e}")
            return None

    async def _get_tag_posts_url(self, session: aiohttp.ClientSession, tags: List[str]) -> List[Dict]:
        """Получение и парсинг постов по сочетанию тегов с использованием Selenium для lazy loading.

        Каждый тег кодируется в URI-формат (включая кириллицу) и объединяется через запятую
        в адресе: /tag/tag1,tag2,tag3
        """
        try:
            sanitized = [t.strip() for t in tags if isinstance(t, str) and t.strip()]
            if not sanitized:
                return []
            encoded_joined = ",".join(quote(t, safe='') for t in sanitized)
            url = f"{self.base_url}/tag/{encoded_joined}"
            
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
            print(f"Ошибка парсинга Pikabu тегов {sanitized}: {e}")
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
    
    async def parse_posts_by_tags(self, tags: Optional[List] = None) -> List[Dict]:
        """Парсинг постов по списку тегов (или self.tags) с использованием Selenium.

        - Теги могут быть кириллическими — кодируются в URI.
        - Поддерживаются группы тегов (массив массивов): [["Бизнес","Негатив"], ["Боли","Бизнес"]].
          Если передан список строк, трактуется как одна группа.
        """
        all_posts = []
        
        async with aiohttp.ClientSession() as session:
            tags_to_process = tags if tags is not None else self.tags
            # Нормализуем в список групп
            if isinstance(tags_to_process, list):
                if all(isinstance(x, list) for x in tags_to_process):
                    groups: List[List[str]] = tags_to_process  # уже массив массивов
                elif all(isinstance(x, str) for x in tags_to_process):
                    groups = [tags_to_process]  # одна группа из переданных тегов
                else:
                    # Смешанный или некорректный формат — падаем назад к одиночным тегам
                    groups = [[str(x)] for x in tags_to_process]
            else:
                groups = [[str(tags_to_process)]]

            for group in groups:
                print(f"Парсинг группы тегов: {group}")
                posts = await self._get_tag_posts_url(session, group)
                
                all_posts.extend(posts)
                print(f"Найдено {len(posts)} постов с болями для группы {group}")
        
        return all_posts

    async def parse_posts_by_tags_csv(self, tags_csv: str) -> List[Dict]:
        """Парсинг постов по тегам, переданным через запятую.

        Примеры:
        - Одна группа: "Бизнес, Негатив, Стартап"
        - Несколько групп (точка с запятой в качестве разделителя групп):
          "Бизнес, Негатив; Боли, Бизнес"
        """
        if not tags_csv:
            return []
        groups_raw = [g for g in (tags_csv.split(';')) if g is not None]
        groups = []
        for g in groups_raw:
            tags_list = [t.strip() for t in g.split(',') if t and t.strip()]
            if tags_list:
                groups.append(tags_list)
        if not groups:
            return []
        return await self.parse_posts_by_tags(tags=groups)
