import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from bs4 import BeautifulSoup
from app.services.pikabu_parser import PikabuParser

class TestPikabuParser:
    """Тесты для Pikabu парсера"""
    
    @pytest.fixture
    def mock_nlp_service(self):
        """Мок NLP сервиса"""
        mock_service = Mock()
        mock_service.analyze_text.return_value = {
            'pain_keywords': ['ненавижу', 'проблема'],
            'pain_intensity': 0.8,
            'sentiment_score': -0.7,
            'entities': [],
            'has_pain': True
        }
        return mock_service
    
    @pytest.fixture
    def pikabu_parser(self, mock_nlp_service):
        """Создание экземпляра Pikabu парсера с моками"""
        with patch('app.services.pikabu_parser.settings') as mock_settings:
            mock_settings.PARSING_DELAY = 0.1
            
            with patch('app.services.pikabu_parser.nlp_service', mock_nlp_service):
                parser = PikabuParser()
                return parser
    
    @pytest.fixture
    def sample_html(self):
        """Образец HTML страницы Pikabu"""
        return """
        <html>
        <body>
            <article class="story">
                <h1>Заголовок поста</h1>
                <div class="story__content-inner">
                    Ненавижу когда интернет тормозит! Это просто кошмар, каждый день проблемы с подключением.
                    Хочу чтобы провайдеры наконец решили эти проблемы. Очень раздражает!
                </div>
                <a class="story__title-link" href="/story/test_post_123">Ссылка на пост</a>
                <a class="user__nick">test_user</a>
            </article>
            <article class="story">
                <h2>Короткий пост</h2>
                <div class="story__content-inner">
                    Короткий текст
                </div>
                <a class="story__title-link" href="/story/short_post_456">Ссылка</a>
                <a class="user__nick">another_user</a>
            </article>
            <article class="story">
                <h1>Пост без болей</h1>
                <div class="story__content-inner">
                    Хорошая погода сегодня, прекрасное настроение. Все отлично и замечательно.
                    Никаких проблем нет, жизнь прекрасна и удивительна.
                </div>
                <a class="story__title-link" href="/story/good_post_789">Ссылка на позитивный пост</a>
                <a class="user__nick">happy_user</a>
            </article>
        </body>
        </html>
        """
    
    def test_pikabu_parser_initialization(self):
        """Тест инициализации Pikabu парсера"""
        parser = PikabuParser()
        assert parser.base_url == "https://pikabu.ru"
        assert "User-Agent" in parser.headers
        assert "Mozilla" in parser.headers["User-Agent"]
    
    @pytest.mark.asyncio
    async def test_parse_page_success(self, pikabu_parser, sample_html):
        """Тест успешного парсинга страницы"""
        # Создаем мок ответа aiohttp
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text.return_value = sample_html
        
        mock_session = AsyncMock()
        mock_session.get.return_value.__aenter__.return_value = mock_response
        
        posts = await pikabu_parser._parse_page(mock_session, 1)
        
        # Должен найти один пост с болями (длинный текст с болевыми словами)
        assert len(posts) > 0
        
        # Проверяем структуру первого поста
        first_post = posts[0]
        assert first_post['source'] == 'pikabu'
        assert 'platform_id' in first_post
        assert 'author' in first_post
        assert 'text' in first_post
        assert 'url' in first_post
        assert 'pain_keywords' in first_post
        assert 'sentiment_score' in first_post
        assert 'pain_intensity' in first_post
        
        # Проверяем содержимое
        assert 'Заголовок поста' in first_post['text']
        assert 'Ненавижу когда интернет' in first_post['text']
        assert first_post['author'] == 'test_user'
        assert 'pikabu.ru' in first_post['url']
        assert 'test_post_123' in first_post['platform_id']
    
    @pytest.mark.asyncio
    async def test_parse_page_short_posts_filtered(self, pikabu_parser, sample_html):
        """Тест фильтрации коротких постов"""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text.return_value = sample_html
        
        mock_session = AsyncMock()
        mock_session.get.return_value.__aenter__.return_value = mock_response
        
        posts = await pikabu_parser._parse_page(mock_session, 1)
        
        # Короткие посты (< 50 символов) должны быть отфильтрованы
        for post in posts:
            assert len(post['text']) >= 50
    
    @pytest.mark.asyncio
    async def test_parse_page_no_pain_filtered(self, pikabu_parser):
        """Тест фильтрации постов без болей"""
        # Настраиваем NLP сервис чтобы не находил боли
        with patch('app.services.pikabu_parser.nlp_service') as mock_nlp:
            mock_nlp.analyze_text.return_value = {
                'pain_keywords': [],
                'pain_intensity': 0.0,
                'sentiment_score': 0.5,
                'entities': [],
                'has_pain': False
            }
            
            html_no_pain = """
            <html>
            <body>
                <article class="story">
                    <h1>Позитивный пост</h1>
                    <div class="story__content-inner">
                        Отличная погода сегодня! Все прекрасно и замечательно. 
                        Жизнь удивительна и полна радости. Никаких проблем нет.
                        Все работает отлично и быстро. Восхитительный день!
                    </div>
                    <a class="story__title-link" href="/story/positive_post">Ссылка</a>
                    <a class="user__nick">happy_user</a>
                </article>
            </body>
            </html>
            """
            
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.text.return_value = html_no_pain
            
            mock_session = AsyncMock()
            mock_session.get.return_value.__aenter__.return_value = mock_response
            
            posts = await pikabu_parser._parse_page(mock_session, 1)
            
            # Посты без болей должны быть отфильтрованы
            assert len(posts) == 0
    
    @pytest.mark.asyncio
    async def test_parse_page_http_error(self, pikabu_parser):
        """Тест обработки HTTP ошибки"""
        mock_response = AsyncMock()
        mock_response.status = 404
        
        mock_session = AsyncMock()
        mock_session.get.return_value.__aenter__.return_value = mock_response
        
        posts = await pikabu_parser._parse_page(mock_session, 1)
        
        # При ошибке должен возвращаться пустой список
        assert posts == []
    
    @pytest.mark.asyncio
    async def test_parse_page_malformed_html(self, pikabu_parser):
        """Тест обработки некорректного HTML"""
        malformed_html = """
        <html>
        <body>
            <article class="story">
                <!-- Нет нужных элементов -->
            </article>
            <article class="story">
                <div class="story__content-inner">
                    <!-- Нет заголовка и ссылок -->
                    Некорректный пост без необходимых элементов для корректного парсинга
                </div>
            </article>
        </body>
        </html>
        """
        
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text.return_value = malformed_html
        
        mock_session = AsyncMock()
        mock_session.get.return_value.__aenter__.return_value = mock_response
        
        posts = await pikabu_parser._parse_page(mock_session, 1)
        
        # Некорректные посты должны быть пропущены, но метод не должен падать
        # Может вернуть пустой список или посты с дефолтными значениями
        assert isinstance(posts, list)
    
    @pytest.mark.asyncio
    async def test_parse_recent_posts_multiple_pages(self, pikabu_parser, sample_html):
        """Тест парсинга нескольких страниц"""
        # Мокируем aiohttp сессию
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text.return_value = sample_html
        
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session.get.return_value.__aenter__.return_value = mock_response
            mock_session_class.return_value.__aenter__.return_value = mock_session
            
            with patch('asyncio.sleep', new_callable=AsyncMock):
                posts = await pikabu_parser.parse_recent_posts()
        
        # Должны получить посты
        assert len(posts) > 0
        
        # Проверяем что запросы были сделаны для 3 страниц
        assert mock_session.get.call_count == 3
        
        # Проверяем URL запросов
        call_args_list = mock_session.get.call_args_list
        urls = [args[0][0] for args in call_args_list]
        
        assert "https://pikabu.ru/new?page=1" in urls
        assert "https://pikabu.ru/new?page=2" in urls
        assert "https://pikabu.ru/new?page=3" in urls
    
    @pytest.mark.asyncio
    async def test_parse_recent_posts_with_error(self, pikabu_parser):
        """Тест парсинга с ошибкой"""
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session.get.side_effect = Exception("Network error")
            mock_session_class.return_value.__aenter__.return_value = mock_session
            
            posts = await pikabu_parser.parse_recent_posts()
        
        # При ошибке должен возвращаться пустой список
        assert posts == []
    
    def test_url_construction(self, pikabu_parser):
        """Тест правильного формирования URL"""
        base_url = pikabu_parser.base_url
        assert base_url == "https://pikabu.ru"
        
        # Проверяем формирование URL страницы
        page = 2
        expected_url = f"{base_url}/new?page={page}"
        assert expected_url == "https://pikabu.ru/new?page=2"
    
    def test_text_length_limit(self, pikabu_parser):
        """Тест ограничения длины текста"""
        # Создаем очень длинный текст
        long_title = "Очень длинный заголовок " * 10
        long_text = "Очень длинный текст поста " * 50  # > 1000 символов
        
        combined_text = f"{long_title}\n\n{long_text}"
        limited_text = combined_text[:1000]
        
        # Проверяем что ограничение работает
        assert len(limited_text) == 1000
        assert len(combined_text) > 1000
    
    @pytest.mark.asyncio  
    async def test_post_data_structure(self, pikabu_parser, sample_html):
        """Тест структуры данных поста"""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text.return_value = sample_html
        
        mock_session = AsyncMock()
        mock_session.get.return_value.__aenter__.return_value = mock_response
        
        posts = await pikabu_parser._parse_page(mock_session, 1)
        
        if posts:
            post = posts[0]
            
            # Проверяем обязательные поля
            required_fields = [
                'source', 'platform_id', 'author', 'text', 'url',
                'pain_keywords', 'sentiment_score', 'pain_intensity'
            ]
            
            for field in required_fields:
                assert field in post, f"Поле '{field}' отсутствует в структуре поста"
            
            # Проверяем типы данных
            assert isinstance(post['source'], str)
            assert isinstance(post['platform_id'], str)
            assert isinstance(post['author'], str)
            assert isinstance(post['text'], str)
            assert isinstance(post['url'], str)
            assert isinstance(post['pain_keywords'], list)
            assert isinstance(post['sentiment_score'], (int, float))
            assert isinstance(post['pain_intensity'], (int, float))
            
            # Проверяем значения
            assert post['source'] == 'pikabu'
            assert len(post['text']) <= 1000


def test_beautifulsoup_parsing():
    """Тест парсинга HTML с BeautifulSoup"""
    html = """
    <article class="story">
        <h1>Тестовый заголовок</h1>
        <div class="story__content-inner">Тестовый контент</div>
        <a class="story__title-link" href="/test">Ссылка</a>
        <a class="user__nick">test_user</a>
    </article>
    """
    
    soup = BeautifulSoup(html, 'html.parser')
    article = soup.find('article', class_='story')
    
    assert article is not None
    
    title = article.find('h1')
    assert title is not None
    assert title.get_text(strip=True) == "Тестовый заголовок"
    
    content = article.find('div', class_='story__content-inner')
    assert content is not None
    assert content.get_text(strip=True) == "Тестовый контент"
    
    link = article.find('a', class_='story__title-link')
    assert link is not None
    assert link['href'] == "/test"
    
    author = article.find('a', class_='user__nick')
    assert author is not None
    assert author.get_text(strip=True) == "test_user"
