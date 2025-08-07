import pytest
from unittest.mock import Mock, patch
from app.services.nlp_service import NLPService

class TestNLPService:
    """Тесты для NLP сервиса"""
    
    @pytest.fixture
    def nlp_service(self):
        """Создание экземпляра NLP сервиса для тестов"""
        with patch('spacy.load') as mock_spacy:
            # Мокируем spacy модель
            mock_nlp = Mock()
            mock_doc = Mock()
            mock_doc.ents = []
            mock_doc.text = ""
            mock_nlp.return_value = mock_doc
            mock_spacy.return_value = mock_nlp
            
            service = NLPService()
            service.nlp = mock_nlp
            return service
    
    def test_find_pain_keywords(self, nlp_service, sample_texts):
        """Тест поиска ключевых слов болей"""
        # Тест с текстом содержащим боли
        pain_text = sample_texts["pain_texts"][0]  # "Ненавижу когда интернет тормозит..."
        keywords = nlp_service._find_pain_keywords(pain_text)
        
        assert len(keywords) > 0
        assert any("ненавижу" in kw.lower() for kw in keywords)
        
        # Тест с нейтральным текстом
        neutral_text = sample_texts["neutral_texts"][0]
        keywords = nlp_service._find_pain_keywords(neutral_text)
        
        assert len(keywords) == 0
    
    def test_calculate_pain_intensity(self, nlp_service):
        """Тест расчета интенсивности боли"""
        # Тест без ключевых слов
        intensity = nlp_service._calculate_pain_intensity([], "простой текст")
        assert intensity == 0.0
        
        # Тест с одним ключевым словом
        intensity = nlp_service._calculate_pain_intensity(["проблема"], "у меня проблема")
        assert 0.0 < intensity <= 1.0
        
        # Тест с усилителями
        intensity_strong = nlp_service._calculate_pain_intensity(
            ["проблема"], 
            "у меня очень серьезная проблема!!!"
        )
        assert intensity_strong > intensity
    
    def test_analyze_sentiment(self, nlp_service):
        """Тест анализа тональности"""
        # Мокируем doc объект
        negative_doc = Mock()
        negative_doc.text = "ужасно плохо кошмар"
        sentiment = nlp_service._analyze_sentiment(negative_doc)
        assert sentiment < 0
        
        positive_doc = Mock()
        positive_doc.text = "отлично прекрасно замечательно"
        sentiment = nlp_service._analyze_sentiment(positive_doc)
        assert sentiment > 0
        
        neutral_doc = Mock()
        neutral_doc.text = "обычный текст без эмоций"
        sentiment = nlp_service._analyze_sentiment(neutral_doc)
        assert sentiment == 0.0
    
    def test_analyze_text_integration(self, nlp_service, sample_texts):
        """Интеграционный тест анализа текста"""
        # Настраиваем мок для spacy
        mock_doc = Mock()
        mock_doc.ents = [Mock(text="банк", label_="ORG")]
        mock_doc.text = sample_texts["pain_texts"][0]
        nlp_service.nlp.return_value = mock_doc
        
        result = nlp_service.analyze_text(sample_texts["pain_texts"][0])
        
        # Проверяем структуру ответа
        assert isinstance(result, dict)
        assert "pain_keywords" in result
        assert "pain_intensity" in result
        assert "sentiment_score" in result
        assert "entities" in result
        assert "has_pain" in result
        
        # Проверяем что боль обнаружена
        assert result["has_pain"] is True
        assert len(result["pain_keywords"]) > 0
        assert result["pain_intensity"] > 0
        
    def test_analyze_text_no_pain(self, nlp_service, sample_texts):
        """Тест анализа текста без болей"""
        # Настраиваем мок для spacy
        mock_doc = Mock()
        mock_doc.ents = []
        mock_doc.text = sample_texts["neutral_texts"][0]
        nlp_service.nlp.return_value = mock_doc
        
        result = nlp_service.analyze_text(sample_texts["neutral_texts"][0])
        
        assert result["has_pain"] is False
        assert len(result["pain_keywords"]) == 0
        assert result["pain_intensity"] == 0.0


def test_nlp_service_initialization():
    """Тест инициализации NLP сервиса"""
    with patch('spacy.load') as mock_spacy:
        mock_nlp = Mock()
        mock_spacy.return_value = mock_nlp
        
        service = NLPService()
        assert service.nlp is not None
        assert hasattr(service, 'pain_patterns')
        
        # Проверяем что паттерны загружены
        assert 'negative_emotions' in service.pain_patterns
        assert 'problems' in service.pain_patterns
        assert 'desires' in service.pain_patterns
        assert 'inconvenience' in service.pain_patterns


def test_nlp_service_spacy_error():
    """Тест обработки ошибки загрузки spaCy модели"""
    with patch('spacy.load', side_effect=OSError("Model not found")):
        with pytest.raises(OSError):
            NLPService()
