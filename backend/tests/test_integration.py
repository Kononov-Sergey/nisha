import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from app.services.nlp_service import NLPService
from app.services.pikabu_parser import PikabuParser  
from app.services.telegram_parser import TelegramParser
from app.services.vk_parcer import VKParser

class TestIntegration:
    """Интеграционные тесты для всей системы парсинга"""
    
    @pytest.fixture
    def real_nlp_service(self):
        """Реальный NLP сервис для интеграционных тестов"""
        with patch('spacy.load') as mock_spacy:
            # Мокируем spacy для тестов
            mock_nlp = Mock()
            mock_doc = Mock()
            mock_doc.ents = []
            mock_spacy.return_value = mock_nlp
            
            service = NLPService()
            service.nlp = mock_nlp
            return service
    
    @pytest.mark.asyncio
    async def test_full_pipeline_vk(self, real_nlp_service):
        """Тест полного пайплайна обработки VK постов"""
        # Мокируем настройки
        with patch('app.services.vk_parcer.settings') as mock_settings:
            mock_settings.VK_ACCESS_TOKEN = "test_token"
            mock_settings.MAX_POSTS_PER_SOURCE = 5
            mock_settings.PARSING_DELAY = 0.1
            
            # Мокируем VK API
            mock_vk_response = {
                'items': [
                    {
                        'id': 123,
                        'owner_id': -12345,
                        'text': 'Ненавижу когда банкоматы не работают! Это настоящая проблема!'
                    },
                    {
                        'id': 124,
                        'owner_id': -12345,
                        'text': 'Хорошая погода сегодня'
                    }
                ]
            }
            
            with patch('vk_api.VkApi') as mock_vk_api:
                mock_api = Mock()
                mock_api.wall.get.return_value = mock_vk_response
                mock_vk_session = Mock()
                mock_vk_session.get_api.return_value = mock_api
                mock_vk_api.return_value = mock_vk_session
                
                # Патчим NLP сервис
                with patch('app.services.vk_parcer.nlp_service', real_nlp_service):
                    parser = VKParser()
                    
                    # Настраиваем NLP ответы
                    def analyze_side_effect(text):
                        if 'ненавижу' in text.lower() or 'проблема' in text.lower():
                            return {
                                'pain_keywords': ['ненавижу', 'проблема'],
                                'pain_intensity': 0.8,
                                'sentiment_score': -0.7,
                                'entities': [],
                                'has_pain': True
                            }
                        else:
                            return {
                                'pain_keywords': [],
                                'pain_intensity': 0.0,
                                'sentiment_score': 0.1,
                                'entities': [],
                                'has_pain': False
                            }
                    
                    real_nlp_service.analyze_text.side_effect = analyze_side_effect
                    
                    # Запускаем парсинг
                    posts = await parser.parse_groups(['test_group'])
                    
                    # Проверяем результат
                    assert len(posts) == 1  # Только пост с болями
                    assert posts[0]['source'] == 'vk'
                    assert posts[0]['has_pain'] == True
                    assert len(posts[0]['pain_keywords']) > 0
    
    @pytest.mark.asyncio
    async def test_full_pipeline_telegram(self, real_nlp_service):
        """Тест полного пайплайна обработки Telegram постов"""
        with patch('app.services.telegram_parser.settings') as mock_settings:
            mock_settings.TGSTAT_TOKEN = "test_token"
            mock_settings.MAX_POSTS_PER_SOURCE = 5
            mock_settings.PARSING_DELAY = 0.1
            mock_settings.PAIN_KEYWORDS = ['проблема', 'бесит']
            
            # Мокируем API ответ
            mock_response_data = {
                'response': {
                    'items': [
                        {
                            'id': 'msg_1',
                            'text': 'Бесит что доставка всегда опаздывает! Серьезная проблема!',
                            'channel': {'title': 'Test Channel'},
                            'link': 'https://t.me/test/1'
                        },
                        {
                            'id': 'msg_2',
                            'text': 'Хорошая погода сегодня',
                            'channel': {'title': 'Test Channel'},
                            'link': 'https://t.me/test/2'
                        }
                    ]
                }
            }
            
            # Мокируем aiohttp
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = mock_response_data
            
            with patch('aiohttp.ClientSession') as mock_session_class:
                mock_session = AsyncMock()
                mock_session.get.return_value.__aenter__.return_value = mock_response
                mock_session_class.return_value.__aenter__.return_value = mock_session
                
                with patch('app.services.telegram_parser.nlp_service', real_nlp_service):
                    parser = TelegramParser()
                    
                    # Настраиваем NLP ответы
                    def analyze_side_effect(text):
                        if 'бесит' in text.lower() or 'проблема' in text.lower():
                            return {
                                'pain_keywords': ['бесит', 'проблема'],
                                'pain_intensity': 0.9,
                                'sentiment_score': -0.8,
                                'entities': [],
                                'has_pain': True
                            }
                        else:
                            return {
                                'pain_keywords': [],
                                'pain_intensity': 0.0,
                                'sentiment_score': 0.2,
                                'entities': [],
                                'has_pain': False
                            }
                    
                    real_nlp_service.analyze_text.side_effect = analyze_side_effect
                    
                    with patch('asyncio.sleep', new_callable=AsyncMock):
                        posts = await parser.parse_channels(['test_channel'])
                    
                    # Проверяем результат
                    assert len(posts) == 1  # Только пост с болями
                    assert posts[0]['source'] == 'telegram'
                    assert posts[0]['has_pain'] == True
                    assert len(posts[0]['pain_keywords']) > 0
    
    @pytest.mark.asyncio
    async def test_full_pipeline_pikabu(self, real_nlp_service):
        """Тест полного пайплайна обработки Pikabu постов"""
        with patch('app.services.pikabu_parser.settings') as mock_settings:
            mock_settings.PARSING_DELAY = 0.1
            
            # Мокируем HTML ответ
            sample_html = """
            <html>
            <body>
                <article class="story">
                    <h1>Проблемы с интернетом</h1>
                    <div class="story__content-inner">
                        Ненавижу когда интернет тормозит! Это серьезная проблема каждый день.
                        Провайдеры должны наконец решить эти вопросы. Очень раздражает!
                    </div>
                    <a class="story__title-link" href="/story/test_post_123">Ссылка на пост</a>
                    <a class="user__nick">angry_user</a>
                </article>
                <article class="story">
                    <h2>Хорошая погода</h2>
                    <div class="story__content-inner">
                        Прекрасная погода сегодня! Все отлично и замечательно. Настроение отличное!
                    </div>
                    <a class="story__title-link" href="/story/good_post_456">Ссылка</a>
                    <a class="user__nick">happy_user</a>
                </article>
            </body>
            </html>
            """
            
            # Мокируем aiohttp
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.text.return_value = sample_html
            
            with patch('aiohttp.ClientSession') as mock_session_class:
                mock_session = AsyncMock()
                mock_session.get.return_value.__aenter__.return_value = mock_response
                mock_session_class.return_value.__aenter__.return_value = mock_session
                
                with patch('app.services.pikabu_parser.nlp_service', real_nlp_service):
                    parser = PikabuParser()
                    
                    # Настраиваем NLP ответы
                    def analyze_side_effect(text):
                        if 'ненавижу' in text.lower() or 'проблема' in text.lower():
                            return {
                                'pain_keywords': ['ненавижу', 'проблема', 'раздражает'],
                                'pain_intensity': 0.85,
                                'sentiment_score': -0.75,
                                'entities': [],
                                'has_pain': True
                            }
                        else:
                            return {
                                'pain_keywords': [],
                                'pain_intensity': 0.0,
                                'sentiment_score': 0.3,
                                'entities': [],
                                'has_pain': False
                            }
                    
                    real_nlp_service.analyze_text.side_effect = analyze_side_effect
                    
                    with patch('asyncio.sleep', new_callable=AsyncMock):
                        posts = await parser.parse_recent_posts()
                    
                    # Проверяем результат
                    assert len(posts) == 1  # Только пост с болями
                    assert posts[0]['source'] == 'pikabu'
                    assert posts[0]['has_pain'] == True
                    assert len(posts[0]['pain_keywords']) > 0
                    assert 'Проблемы с интернетом' in posts[0]['text']
    
    @pytest.mark.asyncio
    async def test_multiple_sources_integration(self, real_nlp_service):
        """Тест интеграции нескольких источников"""
        # Мокируем все сервисы одновременно
        
        # VK
        with patch('app.services.vk_parcer.settings') as vk_settings:
            vk_settings.VK_ACCESS_TOKEN = "test_token"
            vk_settings.MAX_POSTS_PER_SOURCE = 2
            vk_settings.PARSING_DELAY = 0.05
            
            with patch('vk_api.VkApi') as mock_vk_api:
                mock_vk_data = {
                    'items': [{
                        'id': 123,
                        'owner_id': -123,
                        'text': 'VK пост с проблемой!'
                    }]
                }
                mock_api = Mock()
                mock_api.wall.get.return_value = mock_vk_data
                mock_vk_session = Mock()
                mock_vk_session.get_api.return_value = mock_api
                mock_vk_api.return_value = mock_vk_session
        
        # Telegram
        with patch('app.services.telegram_parser.settings') as tg_settings:
            tg_settings.TGSTAT_TOKEN = "test_token"
            tg_settings.MAX_POSTS_PER_SOURCE = 2
            tg_settings.PARSING_DELAY = 0.05
            tg_settings.PAIN_KEYWORDS = ['проблема']
            
            mock_tg_data = {
                'response': {
                    'items': [{
                        'id': 'tg_1',
                        'text': 'Telegram пост с проблемой!',
                        'channel': {'title': 'Test'},
                        'link': 'https://t.me/test/1'
                    }]
                }
            }
        
        # Настраиваем NLP для всех сервисов
        def analyze_side_effect(text):
            if 'проблема' in text.lower():
                return {
                    'pain_keywords': ['проблема'],
                    'pain_intensity': 0.7,
                    'sentiment_score': -0.6,
                    'entities': [],
                    'has_pain': True
                }
            return {
                'pain_keywords': [],
                'pain_intensity': 0.0,
                'sentiment_score': 0.0,
                'entities': [],
                'has_pain': False
            }
        
        real_nlp_service.analyze_text.side_effect = analyze_side_effect
        
        with patch('app.services.vk_parcer.nlp_service', real_nlp_service):
            with patch('app.services.telegram_parser.nlp_service', real_nlp_service):
                # Создаем парсеры
                vk_parser = VKParser()
                
                # Мокируем aiohttp для Telegram
                mock_response = AsyncMock()
                mock_response.status = 200
                mock_response.json.return_value = mock_tg_data
                
                with patch('aiohttp.ClientSession') as mock_session_class:
                    mock_session = AsyncMock()
                    mock_session.get.return_value.__aenter__.return_value = mock_response
                    mock_session_class.return_value.__aenter__.return_value = mock_session
                    
                    tg_parser = TelegramParser()
                    
                    # Запускаем парсинг параллельно
                    with patch('asyncio.sleep', new_callable=AsyncMock):
                        vk_posts, tg_posts = await asyncio.gather(
                            vk_parser.parse_groups(['test_group']),
                            tg_parser.parse_channels(['test_channel'])
                        )
                    
                    # Объединяем результаты
                    all_posts = vk_posts + tg_posts
                    
                    # Проверяем что получили посты от обоих источников
                    assert len(all_posts) == 2
                    
                    sources = [post['source'] for post in all_posts]
                    assert 'vk' in sources
                    assert 'telegram' in sources
                    
                    # Все посты должны содержать боли
                    for post in all_posts:
                        assert post['has_pain'] == True
                        assert len(post['pain_keywords']) > 0
    
    def test_data_consistency_across_sources(self):
        """Тест согласованности структуры данных между источниками"""
        # Ожидаемые поля в каждом посте
        expected_fields = {
            'source', 'platform_id', 'author', 'text', 'url',
            'pain_keywords', 'sentiment_score', 'pain_intensity'
        }
        
        # Создаем тестовые посты от разных источников
        vk_post = {
            'source': 'vk',
            'platform_id': '123',
            'author': 'vk_user',
            'text': 'VK test post',
            'url': 'https://vk.com/test',
            'pain_keywords': ['проблема'],
            'sentiment_score': -0.5,
            'pain_intensity': 0.7
        }
        
        telegram_post = {
            'source': 'telegram',
            'platform_id': 'tg_123',
            'author': 'TG Channel',
            'text': 'Telegram test post',
            'url': 'https://t.me/test/123',
            'pain_keywords': ['бесит'],
            'sentiment_score': -0.6,
            'pain_intensity': 0.8
        }
        
        pikabu_post = {
            'source': 'pikabu',
            'platform_id': 'pikabu_123',
            'author': 'pikabu_user',
            'text': 'Pikabu test post',
            'url': 'https://pikabu.ru/story/test',
            'pain_keywords': ['ненавижу'],
            'sentiment_score': -0.7,
            'pain_intensity': 0.9
        }
        
        all_posts = [vk_post, telegram_post, pikabu_post]
        
        # Проверяем структуру каждого поста
        for post in all_posts:
            post_fields = set(post.keys())
            assert post_fields == expected_fields, f"Несоответствие полей в посте от {post['source']}"
            
            # Проверяем типы данных
            assert isinstance(post['source'], str)
            assert isinstance(post['platform_id'], str)
            assert isinstance(post['author'], str)
            assert isinstance(post['text'], str)
            assert isinstance(post['url'], str)
            assert isinstance(post['pain_keywords'], list)
            assert isinstance(post['sentiment_score'], (int, float))
            assert isinstance(post['pain_intensity'], (int, float))
