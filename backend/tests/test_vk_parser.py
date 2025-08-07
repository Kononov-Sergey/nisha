import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from app.services.vk_parcer import VKParser

class TestVKParser:
    """Тесты для VK парсера"""
    
    @pytest.fixture
    def mock_nlp_service(self):
        """Мок NLP сервиса"""
        mock_service = Mock()
        mock_service.analyze_text.return_value = {
            'pain_keywords': ['проблема', 'бесит'],
            'pain_intensity': 0.7,
            'sentiment_score': -0.5,
            'entities': [],
            'has_pain': True
        }
        return mock_service
    
    @pytest.fixture
    def vk_parser(self, mock_nlp_service):
        """Создание экземпляра VK парсера с моками"""
        with patch('app.services.vk_parcer.settings') as mock_settings:
            mock_settings.VK_ACCESS_TOKEN = "test_token"
            mock_settings.MAX_POSTS_PER_SOURCE = 10
            mock_settings.PARSING_DELAY = 0.1
            
            with patch('app.services.vk_parcer.nlp_service', mock_nlp_service):
                with patch('vk_api.VkApi') as mock_vk_api:
                    mock_api = Mock()
                    mock_vk_session = Mock()
                    mock_vk_session.get_api.return_value = mock_api
                    mock_vk_api.return_value = mock_vk_session
                    
                    parser = VKParser()
                    parser.vk = mock_api
                    return parser
    
    def test_vk_parser_initialization_success(self):
        """Тест успешной инициализации VK парсера"""
        with patch('app.services.vk_parcer.settings') as mock_settings:
            mock_settings.VK_ACCESS_TOKEN = "test_token"
            
            with patch('vk_api.VkApi') as mock_vk_api:
                mock_vk_session = Mock()
                mock_vk_api.return_value = mock_vk_session
                
                parser = VKParser()
                assert parser.vk_session is not None
    
    def test_vk_parser_initialization_no_token(self):
        """Тест инициализации без токена"""
        with patch('app.services.vk_parcer.settings') as mock_settings:
            mock_settings.VK_ACCESS_TOKEN = None
            
            with pytest.raises(ValueError, match="VK_ACCESS_TOKEN не установлен"):
                VKParser()
    
    @pytest.mark.asyncio
    async def test_get_group_posts_success(self, vk_parser, mock_vk_response):
        """Тест успешного получения постов группы"""
        # Настраиваем мок VK API
        vk_parser.vk.wall.get.return_value = mock_vk_response
        
        posts = await vk_parser._get_group_posts("test_group")
        
        # Проверяем что посты получены
        assert len(posts) > 0
        
        # Проверяем структуру первого поста
        first_post = posts[0]
        assert first_post['source'] == 'vk'
        assert 'platform_id' in first_post
        assert 'author' in first_post
        assert 'text' in first_post
        assert 'url' in first_post
        assert 'pain_keywords' in first_post
        assert 'sentiment_score' in first_post
        assert 'pain_intensity' in first_post
        
        # Проверяем что URL сформирован правильно
        assert 'vk.com' in first_post['url']
        assert 'test_group' in first_post['url']
    
    @pytest.mark.asyncio
    async def test_get_group_posts_no_text(self, vk_parser):
        """Тест обработки постов без текста"""
        # Мок ответа с постами без текста
        empty_response = {
            'items': [
                {'id': 1, 'owner_id': -123},  # Нет поля text
                {'id': 2, 'owner_id': -123, 'text': ''},  # Пустой text
            ]
        }
        
        vk_parser.vk.wall.get.return_value = empty_response
        
        posts = await vk_parser._get_group_posts("test_group")
        
        # Посты без текста должны быть отфильтрованы
        assert len(posts) == 0
    
    @pytest.mark.asyncio
    async def test_get_group_posts_no_pain(self, vk_parser):
        """Тест обработки постов без болей"""
        # Настраиваем NLP сервис чтобы не находил боли
        with patch('app.services.vk_parcer.nlp_service') as mock_nlp:
            mock_nlp.analyze_text.return_value = {
                'pain_keywords': [],
                'pain_intensity': 0.0,
                'sentiment_score': 0.0,
                'entities': [],
                'has_pain': False
            }
            
            response = {
                'items': [
                    {
                        'id': 123,
                        'owner_id': -12345,
                        'text': 'Обычный текст без болей'
                    }
                ]
            }
            
            vk_parser.vk.wall.get.return_value = response
            
            posts = await vk_parser._get_group_posts("test_group")
            
            # Посты без болей должны быть отфильтрованы
            assert len(posts) == 0
    
    @pytest.mark.asyncio
    async def test_get_group_posts_api_error(self, vk_parser):
        """Тест обработки ошибки VK API"""
        # Настраиваем мок для выброса исключения
        vk_parser.vk.wall.get.side_effect = Exception("VK API Error")
        
        posts = await vk_parser._get_group_posts("test_group")
        
        # При ошибке должен возвращаться пустой список
        assert posts == []
    
    @pytest.mark.asyncio
    async def test_parse_groups_multiple(self, vk_parser, mock_vk_response):
        """Тест парсинга нескольких групп"""
        vk_parser.vk.wall.get.return_value = mock_vk_response
        
        groups = ["group1", "group2"]
        
        # Мокируем sleep для ускорения теста
        with patch('asyncio.sleep', new_callable=AsyncMock):
            posts = await vk_parser.parse_groups(groups)
        
        # Должны получить посты от всех групп
        assert len(posts) > 0
        
        # Проверяем что метод вызывался для каждой группы
        assert vk_parser.vk.wall.get.call_count == len(groups)
    
    @pytest.mark.asyncio 
    async def test_parse_groups_with_error(self, vk_parser):
        """Тест парсинга групп с ошибкой в одной из них"""
        def side_effect(domain, **kwargs):
            if domain == "error_group":
                raise Exception("API Error")
            return {
                'items': [
                    {
                        'id': 123,
                        'owner_id': -123,
                        'text': 'Тестовый пост с проблемой'
                    }
                ]
            }
        
        vk_parser.vk.wall.get.side_effect = side_effect
        
        groups = ["good_group", "error_group", "another_good_group"]
        
        with patch('asyncio.sleep', new_callable=AsyncMock):
            posts = await vk_parser.parse_groups(groups)
        
        # Должны получить посты от рабочих групп, несмотря на ошибку
        assert len(posts) > 0
    
    def test_url_generation(self, vk_parser, mock_vk_response):
        """Тест правильного формирования URL поста"""
        # Берем тестовые данные
        post_data = mock_vk_response['items'][0]
        domain = "testgroup"
        
        # Формируем URL как в коде
        expected_url = f"https://vk.com/{domain}?w=wall{post_data['owner_id']}_{post_data['id']}"
        
        # Устанавливаем мок
        vk_parser.vk.wall.get.return_value = mock_vk_response
        
        # Получаем посты
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            posts = loop.run_until_complete(vk_parser._get_group_posts(domain))
            
            if posts:
                actual_url = posts[0]['url']
                assert domain in actual_url
                assert str(post_data['id']) in actual_url
                assert str(post_data['owner_id']) in actual_url
        finally:
            loop.close()


def test_mock_integration():
    """Тест интеграции с мок данными"""
    mock_data = {
        'items': [
            {
                'id': 123,
                'owner_id': -12345,
                'text': 'Ненавижу когда банкоматы не работают! Очень неудобно!',
                'date': 1640995200
            }
        ]
    }
    
    # Проверяем что тестовые данные корректные
    assert len(mock_data['items']) > 0
    assert mock_data['items'][0]['text'] != ''
    assert 'id' in mock_data['items'][0]
    assert 'owner_id' in mock_data['items'][0]
