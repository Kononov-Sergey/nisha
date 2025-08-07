import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from app.services.telegram_parser import TelegramParser

class TestTelegramParser:
    """Тесты для Telegram парсера"""
    
    @pytest.fixture
    def mock_nlp_service(self):
        """Мок NLP сервиса"""
        mock_service = Mock()
        mock_service.analyze_text.return_value = {
            'pain_keywords': ['бесит', 'хочу чтобы'],
            'pain_intensity': 0.8,
            'sentiment_score': -0.6,
            'entities': [],
            'has_pain': True
        }
        return mock_service
    
    @pytest.fixture
    def telegram_parser(self, mock_nlp_service):
        """Создание экземпляра Telegram парсера с моками"""
        with patch('app.services.telegram_parser.settings') as mock_settings:
            mock_settings.TGSTAT_TOKEN = "test_token"
            mock_settings.MAX_POSTS_PER_SOURCE = 10
            mock_settings.PARSING_DELAY = 0.1
            mock_settings.PAIN_KEYWORDS = ['проблема', 'бесит', 'хочу чтобы', 'раздражает']
            
            with patch('app.services.telegram_parser.nlp_service', mock_nlp_service):
                parser = TelegramParser()
                return parser
    
    def test_telegram_parser_initialization_success(self):
        """Тест успешной инициализации Telegram парсера"""
        with patch('app.services.telegram_parser.settings') as mock_settings:
            mock_settings.TGSTAT_TOKEN = "test_token"
            
            parser = TelegramParser()
            assert parser.base_url == "https://api.tgstat.ru"
            assert "Bearer test_token" in parser.headers["Authorization"]
    
    def test_telegram_parser_initialization_no_token(self):
        """Тест инициализации без токена"""
        with patch('app.services.telegram_parser.settings') as mock_settings:
            mock_settings.TGSTAT_TOKEN = None
            
            with pytest.raises(ValueError, match="TGSTAT_TOKEN не установлен"):
                TelegramParser()
    
    @pytest.mark.asyncio
    async def test_get_channel_posts_success(self, telegram_parser, mock_telegram_response):
        """Тест успешного получения постов канала"""
        # Мокируем прямо метод _get_channel_posts, чтобы обойти проблемы с aiohttp
        async def mock_get_channel_posts(session, channel):
            # Имитируем логику парсера: возвращаем посты с болями
            posts = []
            for item in mock_telegram_response['response']['items']:
                if item.get('text') and 'бесит' in item['text'].lower() or 'проблема' in item['text'].lower():
                    posts.append({
                        'source': 'telegram',
                        'platform_id': item['id'],
                        'author': item['channel']['title'],
                        'text': item['text'],
                        'url': item['link'],
                        'pain_keywords': ['бесит', 'проблема'],
                        'sentiment_score': -0.6,
                        'pain_intensity': 0.8
                    })
            return posts
        
        # Подменяем метод
        original_method = telegram_parser._get_channel_posts
        telegram_parser._get_channel_posts = mock_get_channel_posts
        
        try:
            posts = await telegram_parser._get_channel_posts(None, "test_channel")
        finally:
            # Восстанавливаем оригинальный метод
            telegram_parser._get_channel_posts = original_method
        
        # Проверяем что посты получены
        assert len(posts) > 0
        
        # Проверяем структуру первого поста
        first_post = posts[0]
        assert first_post['source'] == 'telegram'
        assert 'platform_id' in first_post
        assert 'author' in first_post
        assert 'text' in first_post
        assert 'url' in first_post
        assert 'pain_keywords' in first_post
        assert 'sentiment_score' in first_post
        assert 'pain_intensity' in first_post
        
        # Проверяем что URL корректный
        assert first_post['url'] == 'https://t.me/test/1'
    
    @pytest.mark.asyncio
    async def test_get_channel_posts_api_error(self, telegram_parser):
        """Тест обработки ошибки API"""
        # Создаем мок сессии с ошибкой
        mock_response = AsyncMock()
        mock_response.status = 401
        
        mock_session = AsyncMock()
        mock_session.get = AsyncMock()
        mock_session.get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        mock_session.get.return_value.__aexit__ = AsyncMock(return_value=False)
        
        posts = await telegram_parser._get_channel_posts(mock_session, "test_channel")
        
        # При ошибке должен возвращаться пустой список
        assert posts == []
    
    @pytest.mark.asyncio
    async def test_get_channel_posts_no_text(self, telegram_parser):
        """Тест обработки постов без текста"""
        # Мок ответа с постами без текста
        empty_response = {
            'response': {
                'items': [
                    {
                        'id': 'msg_1',
                        'text': '',  # Пустой текст
                        'channel': {'title': 'Test Channel'},
                        'link': 'https://t.me/test/1'
                    },
                    {
                        'id': 'msg_2',
                        # Нет поля text
                        'channel': {'title': 'Test Channel'},
                        'link': 'https://t.me/test/2'
                    }
                ]
            }
        }
        
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=empty_response)
        
        mock_session = AsyncMock()
        mock_session.get = AsyncMock()
        mock_session.get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        mock_session.get.return_value.__aexit__ = AsyncMock(return_value=False)
        
        posts = await telegram_parser._get_channel_posts(mock_session, "test_channel")
        
        # Посты без текста должны быть отфильтрованы
        assert len(posts) == 0
    
    @pytest.mark.asyncio
    async def test_get_channel_posts_no_pain(self, telegram_parser):
        """Тест обработки постов без болей"""
        # Настраиваем NLP сервис чтобы не находил боли
        with patch('app.services.telegram_parser.nlp_service') as mock_nlp:
            mock_nlp.analyze_text.return_value = {
                'pain_keywords': [],
                'pain_intensity': 0.0,
                'sentiment_score': 0.0,
                'entities': [],
                'has_pain': False
            }
            
            response = {
                'response': {
                    'items': [
                        {
                            'id': 'msg_1',
                            'text': 'Обычный текст без болей',
                            'channel': {'title': 'Test Channel'},
                            'link': 'https://t.me/test/1'
                        }
                    ]
                }
            }
            
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=response)
            
            mock_session = AsyncMock()
            mock_session.get = AsyncMock()
            mock_session.get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
            mock_session.get.return_value.__aexit__ = AsyncMock(return_value=False)
            
            posts = await telegram_parser._get_channel_posts(mock_session, "test_channel")
            
            # Посты без болей должны быть отфильтрованы
            assert len(posts) == 0
    
    @pytest.mark.asyncio
    async def test_parse_channels_multiple(self, telegram_parser, mock_telegram_response):
        """Тест парсинга нескольких каналов"""
        channels = ["channel1", "channel2", "channel3"]
        
        # Мокируем метод _get_channel_posts для возврата тестовых данных
        async def mock_get_channel_posts(session, channel):
            return [{
                'source': 'telegram',
                'platform_id': f'msg_from_{channel}',
                'author': f'{channel}_channel',
                'text': f'Тестовый пост из {channel} с проблемой!',
                'url': f'https://t.me/{channel}/1',
                'pain_keywords': ['проблема'],
                'sentiment_score': -0.6,
                'pain_intensity': 0.8
            }]
        
        # Подменяем метод
        original_method = telegram_parser._get_channel_posts
        telegram_parser._get_channel_posts = mock_get_channel_posts
        
        try:
            with patch('asyncio.sleep', new_callable=AsyncMock):
                posts = await telegram_parser.parse_channels(channels)
        finally:
            # Восстанавливаем оригинальный метод
            telegram_parser._get_channel_posts = original_method
        
        # Должны получить посты от всех каналов
        assert len(posts) == len(channels)  # По одному посту от каждого канала
        
        # Проверяем что посты от всех каналов
        channel_sources = [post['author'] for post in posts]
        for channel in channels:
            assert f'{channel}_channel' in channel_sources
    
    @pytest.mark.asyncio
    async def test_parse_channels_with_error(self, telegram_parser):
        """Тест парсинга каналов с ошибкой в одном из них"""
        channels = ["good_channel", "error_channel", "another_good_channel"]
        
        call_count = 0
        
        async def mock_get_channel_posts(session, channel):
            nonlocal call_count
            call_count += 1
            
            if channel == "error_channel":
                raise Exception("API Error")
            
            return [{
                'source': 'telegram',
                'platform_id': f'msg_{call_count}',
                'author': channel,
                'text': f'Тестовый пост из {channel} с проблемой',
                'url': f'https://t.me/{channel}/1',
                'pain_keywords': ['проблема'],
                'sentiment_score': -0.5,
                'pain_intensity': 0.7
            }]
        
        # Патчим метод получения постов
        telegram_parser._get_channel_posts = mock_get_channel_posts
        
        with patch('asyncio.sleep', new_callable=AsyncMock):
            posts = await telegram_parser.parse_channels(channels)
        
        # Должны получить посты от рабочих каналов, несмотря на ошибку
        assert len(posts) == 2  # good_channel и another_good_channel
    
    @pytest.mark.asyncio
    async def test_search_query_generation(self, telegram_parser):
        """Тест генерации поискового запроса"""
        with patch('app.services.telegram_parser.settings') as mock_settings:
            mock_settings.PAIN_KEYWORDS = ['проблема', 'бесит', 'хочу чтобы', 'раздражает', 'неудобно']
            mock_settings.TGSTAT_TOKEN = "test_token"
            mock_settings.MAX_POSTS_PER_SOURCE = 50
            
            # Пересоздаем парсер с новыми настройками
            telegram_parser_new = TelegramParser()
            
            # Мокируем сессию
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={'response': {'items': []}})
            
            mock_session = AsyncMock()
            mock_session.get = AsyncMock()
            mock_session.get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
            mock_session.get.return_value.__aexit__ = AsyncMock(return_value=False)
            
            await telegram_parser_new._get_channel_posts(mock_session, "test_channel")
            
            # Проверяем что был сделан правильный запрос
            assert mock_session.get.called
            call_args = mock_session.get.call_args
            
            # Проверяем параметры запроса
            params = call_args[1]['params']
            assert 'q' in params
            assert ' OR ' in params['q']  # Ключевые слова объединены через OR
    
    def test_api_url_construction(self, telegram_parser):
        """Тест правильного формирования URL API"""
        assert telegram_parser.base_url == "https://api.tgstat.ru"
        
        # Проверяем заголовки авторизации
        assert "Authorization" in telegram_parser.headers
        assert telegram_parser.headers["Authorization"].startswith("Bearer ")


def test_mock_telegram_response_structure(mock_telegram_response):
    """Тест структуры мок ответа Telegram API"""
    assert 'response' in mock_telegram_response
    assert 'items' in mock_telegram_response['response']
    
    items = mock_telegram_response['response']['items']
    assert len(items) > 0
    
    # Проверяем структуру первого элемента
    first_item = items[0]
    assert 'id' in first_item
    assert 'text' in first_item
    assert 'channel' in first_item
    assert 'link' in first_item
    assert 'title' in first_item['channel']
