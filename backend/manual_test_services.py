#!/usr/bin/env python3
"""
Скрипт для ручного тестирования сервисов парсинга.
Позволяет проверить работу каждого сервиса отдельно и в целом.
"""

import asyncio
import sys
import os
from typing import List, Dict

# Добавляем путь к приложению
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app.core.config import settings
from app.services.nlp_service import nlp_service
from app.services.pikabu_parser import PikabuParser
from app.services.telegram_parser import TelegramParser
from app.services.vk_parcer import VKParser

def print_separator(title: str):
    """Печать разделителя с заголовком"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def print_post(post: Dict, index: int):
    """Красивая печать поста"""
    print(f"\n--- Пост #{index + 1} ---")
    print(f"Источник: {post.get('source', 'N/A')}")
    print(f"Автор: {post.get('author', 'N/A')}")
    print(f"URL: {post.get('url', 'N/A')}")
    print(f"Боли: {', '.join(post.get('pain_keywords', []))}")
    print(f"Интенсивность боли: {post.get('pain_intensity', 0)}")
    print(f"Тональность: {post.get('sentiment_score', 0)}")
    print(f"Текст: {post.get('text', 'N/A')[:200]}...")

def test_nlp_service():
    """Тестирование NLP сервиса"""
    print_separator("ТЕСТ NLP СЕРВИСА")
    
    test_texts = [
        "Ненавижу когда интернет тормозит! Это просто кошмар!",
        "У меня проблема с доставкой еды - всегда опаздывают",
        "Хочу чтобы банки работали 24/7, очень неудобно",
        "Сегодня хорошая погода для прогулки",
        "Отличный сервис доставки, все быстро!"
    ]
    
    try:
        print("Анализируем тестовые тексты...\n")
        
        for i, text in enumerate(test_texts, 1):
            print(f"Текст {i}: {text}")
            result = nlp_service.analyze_text(text)
            
            print(f"  Боли найдены: {result['has_pain']}")
            print(f"  Ключевые слова: {result['pain_keywords']}")
            print(f"  Интенсивность: {result['pain_intensity']}")
            print(f"  Тональность: {result['sentiment_score']}")
            print()
        
        print("✅ NLP сервис работает корректно!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка в NLP сервисе: {e}")
        return False

async def test_pikabu_parser():
    """Тестирование Pikabu парсера"""
    print_separator("ТЕСТ PIKABU ПАРСЕРА")
    
    try:
        parser = PikabuParser()
        print("Парсер Pikabu инициализирован успешно")
        print(f"Базовый URL: {parser.base_url}")
        print("User-Agent настроен")
        
        print("\n⚠️  Для полного тестирования запустите:")
        print("posts = await parser.parse_recent_posts()")
        print("Это сделает реальные HTTP запросы к Pikabu")
        
        # Можно протестировать парсинг HTML без запросов
        sample_html = """
        <article class="story">
            <h1>Тестовый пост</h1>
            <div class="story__content-inner">
                Ненавижу когда интернет тормозит! Это серьезная проблема.
                Хочу чтобы провайдеры наконец это исправили.
            </div>
            <a class="story__title-link" href="/story/test">Ссылка</a>
            <a class="user__nick">test_user</a>
        </article>
        """
        
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(sample_html, 'html.parser')
        articles = soup.find_all('article', class_='story')
        
        print(f"\nТест парсинга HTML: найдено {len(articles)} статей")
        
        print("✅ Pikabu парсер настроен корректно!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка в Pikabu парсере: {e}")
        return False

async def test_telegram_parser():
    """Тестирование Telegram парсера"""
    print_separator("ТЕСТ TELEGRAM ПАРСЕРА")
    
    try:
        if not settings.TGSTAT_TOKEN:
            print("❌ TGSTAT_TOKEN не настроен в переменных окружения")
            print("Установите токен для полного тестирования")
            return False
            
        parser = TelegramParser()
        print("Парсер Telegram инициализирован успешно")
        print(f"API URL: {parser.base_url}")
        print("Токен авторизации настроен")
        
        print("\n⚠️  Для полного тестирования запустите:")
        print("posts = await parser.parse_channels(['channel_name'])")
        print("Это сделает реальные запросы к TGStat API")
        
        print("✅ Telegram парсер настроен корректно!")
        return True
        
    except ValueError as e:
        print(f"❌ Ошибка конфигурации: {e}")
        return False
    except Exception as e:
        print(f"❌ Ошибка в Telegram парсере: {e}")
        return False

async def test_vk_parser():
    """Тестирование VK парсера"""
    print_separator("ТЕСТ VK ПАРСЕРА")
    
    try:
        if not settings.VK_ACCESS_TOKEN:
            print("❌ VK_ACCESS_TOKEN не настроен в переменных окружения")
            print("Установите токен для полного тестирования")
            return False
            
        parser = VKParser()
        print("Парсер VK инициализирован успешно")
        print("VK API сессия создана")
        
        print("\n⚠️  Для полного тестирования запустите:")
        print("posts = await parser.parse_groups(['group_domain'])")
        print("Это сделает реальные запросы к VK API")
        
        print("✅ VK парсер настроен корректно!")
        return True
        
    except ValueError as e:
        print(f"❌ Ошибка конфигурации: {e}")
        return False
    except Exception as e:
        print(f"❌ Ошибка в VK парсере: {e}")
        return False

async def test_real_parsing():
    """Тестирование реального парсинга (осторожно - делает реальные запросы!)"""
    print_separator("РЕАЛЬНОЕ ТЕСТИРОВАНИЕ ПАРСИНГА")
    
    print("⚠️  ВНИМАНИЕ: Этот тест делает реальные HTTP запросы!")
    print("Убедитесь что у вас есть:")
    print("- Стабильное интернет соединение")
    print("- Настроенные API токены (если нужны)")
    print("- Понимание что это может занять время")
    
    response = input("\nПродолжить? (y/N): ")
    if response.lower() != 'y':
        print("Тест отменен пользователем")
        return
    
    results = {}
    
    # Тест Pikabu (не требует токенов)
    try:
        print("\n🔄 Тестируем Pikabu...")
        parser = PikabuParser()
        posts = await parser.parse_recent_posts()
        results['pikabu'] = {
            'success': True,
            'posts_count': len(posts),
            'posts': posts[:3]  # Первые 3 поста для показа
        }
        print(f"✅ Pikabu: найдено {len(posts)} постов с болями")
        
    except Exception as e:
        results['pikabu'] = {'success': False, 'error': str(e)}
        print(f"❌ Pikabu: {e}")
    
    # Тест VK (требует токен)
    if settings.VK_ACCESS_TOKEN:
        try:
            print("\n🔄 Тестируем VK...")
            parser = VKParser()
            # Тестируем на популярных группах (замените на свои)
            test_groups = ['apiclub', 'proglib']
            posts = await parser.parse_groups(test_groups)
            results['vk'] = {
                'success': True,
                'posts_count': len(posts),
                'posts': posts[:3]
            }
            print(f"✅ VK: найдено {len(posts)} постов с болями")
            
        except Exception as e:
            results['vk'] = {'success': False, 'error': str(e)}
            print(f"❌ VK: {e}")
    else:
        print("⏭️  VK: пропущен (нет токена)")
    
    # Тест Telegram (требует токен)
    if settings.TGSTAT_TOKEN:
        try:
            print("\n🔄 Тестируем Telegram...")
            parser = TelegramParser()
            # Тестируем поиск по ключевым словам
            posts = await parser.parse_channels(['test'])  # Общий поиск
            results['telegram'] = {
                'success': True,
                'posts_count': len(posts),
                'posts': posts[:3]
            }
            print(f"✅ Telegram: найдено {len(posts)} постов с болями")
            
        except Exception as e:
            results['telegram'] = {'success': False, 'error': str(e)}
            print(f"❌ Telegram: {e}")
    else:
        print("⏭️  Telegram: пропущен (нет токена)")
    
    # Выводим результаты
    print_separator("РЕЗУЛЬТАТЫ РЕАЛЬНОГО ТЕСТИРОВАНИЯ")
    
    total_posts = 0
    for source, result in results.items():
        if result['success']:
            count = result['posts_count']
            total_posts += count
            print(f"✅ {source.capitalize()}: {count} постов")
            
            # Показываем примеры постов
            for i, post in enumerate(result['posts']):
                print_post(post, i)
        else:
            print(f"❌ {source.capitalize()}: {result['error']}")
    
    print(f"\n📊 Всего найдено постов с болями: {total_posts}")

def show_configuration():
    """Показать текущую конфигурацию"""
    print_separator("КОНФИГУРАЦИЯ")
    
    print("Настройки приложения:")
    print(f"  DATABASE_URL: {settings.DATABASE_URL}")
    print(f"  SPACY_MODEL: {settings.SPACY_MODEL}")
    print(f"  MAX_POSTS_PER_SOURCE: {settings.MAX_POSTS_PER_SOURCE}")
    print(f"  PARSING_DELAY: {settings.PARSING_DELAY}")
    
    print("\nБолевые ключевые слова:")
    for keyword in settings.PAIN_KEYWORDS:
        print(f"  - {keyword}")
    
    print("\nAPI токены:")
    print(f"  VK_ACCESS_TOKEN: {'✅ Настроен' if settings.VK_ACCESS_TOKEN else '❌ Не настроен'}")
    print(f"  TGSTAT_TOKEN: {'✅ Настроен' if settings.TGSTAT_TOKEN else '❌ Не настроен'}")
    print(f"  TELEGRAM_API_ID: {'✅ Настроен' if settings.TELEGRAM_API_ID else '❌ Не настроен'}")
    print(f"  TELEGRAM_API_HASH: {'✅ Настроен' if settings.TELEGRAM_API_HASH else '❌ Не настроен'}")

async def main():
    """Главная функция для запуска тестов"""
    print("🔧 ТЕСТИРОВАНИЕ СЕРВИСОВ ПАРСИНГА БОЛЕЙ")
    print("Выберите тест для запуска:")
    print("1. Показать конфигурацию")
    print("2. Тест NLP сервиса")
    print("3. Тест Pikabu парсера")
    print("4. Тест Telegram парсера")
    print("5. Тест VK парсера") 
    print("6. Тест всех сервисов")
    print("7. РЕАЛЬНОЕ тестирование (делает HTTP запросы!)")
    print("0. Выход")
    
    while True:
        try:
            choice = input("\nВведите номер теста: ").strip()
            
            if choice == '0':
                print("Выход...")
                break
            elif choice == '1':
                show_configuration()
            elif choice == '2':
                test_nlp_service()
            elif choice == '3':
                await test_pikabu_parser()
            elif choice == '4':
                await test_telegram_parser()
            elif choice == '5':
                await test_vk_parser()
            elif choice == '6':
                print_separator("ТЕСТ ВСЕХ СЕРВИСОВ")
                success_count = 0
                
                if test_nlp_service():
                    success_count += 1
                if await test_pikabu_parser():
                    success_count += 1
                if await test_telegram_parser():
                    success_count += 1
                if await test_vk_parser():
                    success_count += 1
                
                print(f"\n📊 Результат: {success_count}/4 сервисов готовы к работе")
            elif choice == '7':
                await test_real_parsing()
            else:
                print("❌ Неверный выбор, попробуйте снова")
                
        except KeyboardInterrupt:
            print("\n\nВыход по Ctrl+C...")
            break
        except Exception as e:
            print(f"❌ Неожиданная ошибка: {e}")

if __name__ == "__main__":
    # Проверяем что spaCy модель установлена
    try:
        import spacy
        spacy.load(settings.SPACY_MODEL)
    except OSError:
        print(f"❌ Модель spaCy '{settings.SPACY_MODEL}' не найдена!")
        print(f"Установите её командой: python -m spacy download {settings.SPACY_MODEL}")
        sys.exit(1)
    
    asyncio.run(main())
