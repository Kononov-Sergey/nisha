# Руководство по тестированию сервисов парсинга

## Обзор

Этот проект включает комплексную систему тестирования для всех сервисов парсинга болей пользователей из социальных сетей:

- **NLP сервис** - анализ текста и детекция болей
- **VK парсер** - парсинг постов из групп ВКонтакте
- **Telegram парсер** - парсинг постов из Telegram каналов
- **Pikabu парсер** - парсинг постов с сайта Pikabu

## Структура тестов

```
tests/
├── __init__.py              # Инициализация пакета тестов
├── conftest.py              # Общие фикстуры и настройки pytest
├── test_nlp_service.py      # Тесты NLP сервиса
├── test_vk_parser.py        # Тесты VK парсера
├── test_telegram_parser.py  # Тесты Telegram парсера
├── test_pikabu_parser.py    # Тесты Pikabu парсера
└── test_integration.py      # Интеграционные тесты
```

## Подготовка к тестированию

### 1. Установка зависимостей

```bash
# Установка основных зависимостей
pip install -r requirements.txt

# Дополнительно для анализа покрытия
pip install pytest-cov
```

### 2. Установка spaCy модели

```bash
python -m spacy download ru_core_news_lg
```

### 3. Настройка переменных окружения (опционально)

Создайте файл `.env` в корне backend папки:

```env
# API ключи (для реального тестирования)
VK_ACCESS_TOKEN=your_vk_token
TGSTAT_TOKEN=your_tgstat_token

# Настройки
SPACY_MODEL=ru_core_news_lg
MAX_POSTS_PER_SOURCE=10
PARSING_DELAY=1.0
```

## Способы запуска тестов

### 1. Автоматические юнит-тесты

#### Все тесты сразу:
```bash
python run_tests.py
```

#### Конкретный сервис:
```bash
# Только NLP сервис
python -m pytest tests/test_nlp_service.py -v

# Только VK парсер
python -m pytest tests/test_vk_parser.py -v

# Только Telegram парсер
python -m pytest tests/test_telegram_parser.py -v

# Только Pikabu парсер
python -m pytest tests/test_pikabu_parser.py -v

# Интеграционные тесты
python -m pytest tests/test_integration.py -v
```

#### С анализом покрытия:
```bash
python -m pytest tests/ --cov=app --cov-report=html --cov-report=term-missing
```

### 2. Ручное интерактивное тестирование

```bash
python manual_test_services.py
```

Этот скрипт предоставляет интерактивное меню для:
- Проверки конфигурации
- Тестирования каждого сервиса отдельно
- Реального тестирования с HTTP запросами

## Описание тестов

### NLP сервис (`test_nlp_service.py`)

**Что тестируется:**
- Инициализация сервиса
- Поиск ключевых слов болей
- Расчет интенсивности боли
- Анализ тональности
- Обработка ошибок

**Пример теста:**
```python
def test_find_pain_keywords(nlp_service):
    text = "Ненавижу когда интернет тормозит!"
    keywords = nlp_service._find_pain_keywords(text)
    assert len(keywords) > 0
    assert any("ненавижу" in kw.lower() for kw in keywords)
```

### VK парсер (`test_vk_parser.py`)

**Что тестируется:**
- Инициализация с токеном и без
- Парсинг постов групп
- Фильтрация по болям
- Обработка ошибок API
- Формирование URL

**Моки:** VK API ответы, NLP сервис

### Telegram парсер (`test_telegram_parser.py`)

**Что тестируется:**
- Инициализация с токеном TGStat
- Поиск постов по ключевым словам
- Обработка API ответов
- Фильтрация контента
- Генерация поисковых запросов

**Моки:** HTTP запросы к TGStat API, NLP сервис

### Pikabu парсер (`test_pikabu_parser.py`)

**Что тестируется:**
- Парсинг HTML страниц
- Извлечение данных постов
- Фильтрация по длине текста
- Обработка некорректного HTML
- Формирование URL

**Моки:** HTTP ответы с HTML, NLP сервис

### Интеграционные тесты (`test_integration.py`)

**Что тестируется:**
- Полный пайплайн обработки для каждого источника
- Интеграция между NLP и парсерами
- Согласованность структуры данных
- Параллельная работа нескольких источников

## Интерпретация результатов

### Успешные тесты
```
tests/test_nlp_service.py::TestNLPService::test_analyze_text_integration PASSED
tests/test_vk_parser.py::TestVKParser::test_parse_groups_multiple PASSED
```

### Типичные ошибки и решения

#### 1. Ошибка spaCy модели
```
OSError: Model 'ru_core_news_lg' not found
```
**Решение:** `python -m spacy download ru_core_news_lg`

#### 2. Отсутствие зависимостей
```
ModuleNotFoundError: No module named 'pytest'
```
**Решение:** `pip install pytest pytest-asyncio`

#### 3. Ошибки конфигурации
```
ValueError: VK_ACCESS_TOKEN не установлен
```
**Решение:** Это ожидаемое поведение в тестах без реальных токенов

## Реальное тестирование

⚠️ **ВНИМАНИЕ:** Реальное тестирование делает HTTP запросы к внешним API!

### Требования:
- Стабильное интернет соединение
- API токены (для VK и Telegram)
- Понимание лимитов API

### Запуск:
```bash
python manual_test_services.py
# Выберите опцию "7. РЕАЛЬНОЕ тестирование"
```

### Ожидаемые результаты:
- **Pikabu:** 10-50 постов с болями (работает без токенов)
- **VK:** 5-30 постов (требует токен)
- **Telegram:** 0-20 постов (требует токен TGStat)

## Мониторинг качества

### Покрытие кода
```bash
python -m pytest tests/ --cov=app --cov-report=html
open htmlcov/index.html  # Просмотр отчета
```

**Целевое покрытие:** >80% для каждого сервиса

### Метрики качества
- Все тесты должны проходить
- Время выполнения тестов < 30 сек
- Нет предупреждений pytest
- Покрытие кода > 80%

## Непрерывная интеграция

Для CI/CD систем используйте:

```bash
# Быстрые тесты без внешних запросов
python -m pytest tests/ -v --tb=short

# С покрытием для отчетов
python -m pytest tests/ --cov=app --cov-report=xml
```

## Отладка тестов

### Подробный вывод:
```bash
python -m pytest tests/test_nlp_service.py -v -s
```

### Остановка на первой ошибке:
```bash
python -m pytest tests/ -x
```

### Запуск конкретного теста:
```bash
python -m pytest tests/test_nlp_service.py::TestNLPService::test_analyze_text_integration -v
```

## Добавление новых тестов

### Шаблон теста сервиса:
```python
import pytest
from unittest.mock import Mock, patch
from app.services.your_service import YourService

class TestYourService:
    @pytest.fixture
    def service(self):
        # Настройка тестового экземпляра
        return YourService()
    
    def test_basic_functionality(self, service):
        # Тест основной функциональности
        result = service.some_method("test_input")
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_async_method(self, service):
        # Тест асинхронного метода
        result = await service.async_method()
        assert isinstance(result, list)
```

### Лучшие практики:
1. Используйте моки для внешних зависимостей
2. Тестируйте как успешные, так и ошибочные сценарии
3. Проверяйте структуру возвращаемых данных
4. Добавляйте docstring к тестам
5. Группируйте связанные тесты в классы

## Контакты

При возникновении проблем с тестами:
1. Проверьте этот документ
2. Убедитесь в правильности установки зависимостей
3. Проверьте логи тестов на наличие подробностей ошибок
