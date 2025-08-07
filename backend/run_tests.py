#!/usr/bin/env python3
"""
Скрипт для запуска автоматических тестов сервисов парсинга.
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """Запуск команды с описанием"""
    print(f"\n🔄 {description}")
    print(f"Команда: {' '.join(command)}")
    print("-" * 50)
    
    try:
        result = subprocess.run(
            command,
            cwd=Path(__file__).parent,
            check=True,
            capture_output=False,
            text=True
        )
        print(f"✅ {description} - успешно!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - ошибка! Код: {e.returncode}")
        return False
    except FileNotFoundError:
        print(f"❌ Команда не найдена: {command[0]}")
        return False

def check_requirements():
    """Проверка установленных зависимостей"""
    print("🔍 Проверка зависимостей...")
    
    required_packages = ['pytest', 'pytest-asyncio']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package} установлен")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package} не установлен")
    
    if missing_packages:
        print(f"\n📦 Установите недостающие пакеты:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    return True

def run_tests():
    """Запуск всех тестов"""
    print("🧪 ЗАПУСК АВТОМАТИЧЕСКИХ ТЕСТОВ")
    print("=" * 60)
    
    # Проверяем зависимости
    if not check_requirements():
        print("\n❌ Сначала установите зависимости")
        return False
    
    # Определяем тесты для запуска
    test_configs = [
        {
            'command': ['python', '-m', 'pytest', 'tests/test_nlp_service.py', '-v'],
            'description': 'Тесты NLP сервиса'
        },
        {
            'command': ['python', '-m', 'pytest', 'tests/test_vk_parser.py', '-v'],
            'description': 'Тесты VK парсера'
        },
        {
            'command': ['python', '-m', 'pytest', 'tests/test_telegram_parser.py', '-v'],
            'description': 'Тесты Telegram парсера'
        },
        {
            'command': ['python', '-m', 'pytest', 'tests/test_pikabu_parser.py', '-v'],
            'description': 'Тесты Pikabu парсера'
        },
        {
            'command': ['python', '-m', 'pytest', 'tests/test_integration.py', '-v'],
            'description': 'Интеграционные тесты'
        }
    ]
    
    # Запускаем тесты
    success_count = 0
    total_count = len(test_configs)
    
    for config in test_configs:
        if run_command(config['command'], config['description']):
            success_count += 1
    
    # Общий результат
    print("\n" + "=" * 60)
    print(f"📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ")
    print(f"Успешно: {success_count}/{total_count}")
    
    if success_count == total_count:
        print("🎉 Все тесты прошли успешно!")
        return True
    else:
        print("⚠️  Некоторые тесты не прошли")
        return False

def run_specific_test():
    """Запуск конкретного теста"""
    print("Выберите тест для запуска:")
    print("1. NLP сервис")
    print("2. VK парсер")  
    print("3. Telegram парсер")
    print("4. Pikabu парсер")
    print("5. Интеграционные тесты")
    print("6. Все тесты")
    print("0. Назад")
    
    choice = input("\nВведите номер: ").strip()
    
    test_map = {
        '1': ('tests/test_nlp_service.py', 'NLP сервиса'),
        '2': ('tests/test_vk_parser.py', 'VK парсера'),
        '3': ('tests/test_telegram_parser.py', 'Telegram парсера'),
        '4': ('tests/test_pikabu_parser.py', 'Pikabu парсера'),
        '5': ('tests/test_integration.py', 'интеграционных'),
    }
    
    if choice == '6':
        return run_tests()
    elif choice == '0':
        return True
    elif choice in test_map:
        test_file, test_name = test_map[choice]
        command = ['python', '-m', 'pytest', test_file, '-v', '-s']
        return run_command(command, f'Тесты {test_name}')
    else:
        print("❌ Неверный выбор")
        return False

def run_coverage():
    """Запуск тестов с покрытием кода"""
    print("📈 Запуск тестов с анализом покрытия кода")
    
    # Проверяем наличие pytest-cov
    try:
        import pytest_cov
        print("✅ pytest-cov установлен")
    except ImportError:
        print("❌ pytest-cov не установлен")
        print("Установите: pip install pytest-cov")
        return False
    
    command = [
        'python', '-m', 'pytest',
        'tests/',
        '--cov=app',
        '--cov-report=html',
        '--cov-report=term-missing',
        '-v'
    ]
    
    success = run_command(command, 'Тесты с покрытием кода')
    
    if success:
        print("\n📊 Отчет о покрытии создан в htmlcov/index.html")
    
    return success

def main():
    """Главная функция"""
    print("🧪 ТЕСТИРОВАНИЕ СЕРВИСОВ ПАРСИНГА")
    print("Выберите режим:")
    print("1. Запустить все тесты")
    print("2. Запустить конкретный тест")
    print("3. Запустить с анализом покрытия")
    print("4. Проверить зависимости")
    print("0. Выход")
    
    while True:
        try:
            choice = input("\nВведите номер: ").strip()
            
            if choice == '0':
                print("Выход...")
                break
            elif choice == '1':
                run_tests()
            elif choice == '2':
                run_specific_test()
            elif choice == '3':
                run_coverage()
            elif choice == '4':
                check_requirements()
            else:
                print("❌ Неверный выбор, попробуйте снова")
                
        except KeyboardInterrupt:
            print("\n\nВыход по Ctrl+C...")
            break
        except Exception as e:
            print(f"❌ Неожиданная ошибка: {e}")

if __name__ == "__main__":
    main()
