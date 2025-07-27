## Струкрутра проекта

```
nisha/
├── frontend/ # Ваш готовый фронтенд
├── backend/
│ ├── app/
│ │ ├── __init__.py
│ │ ├── main.py # Основное FastAPI приложение
│ │ ├── core/ # Конфигурации и настройки
│ │ │ ├── __init__.py
│ │ │ ├── config.py # Настройки приложения
│ │ │ └── database.py # Настройки БД
│ │ ├── models/ # SQLAlchemy модели БД
│ │ │ ├── __init__.py
│ │ │ └── pain_post.py # Модель найденного поста
│ │ ├── schemas/ # Pydantic схемы для API
│ │ │ ├── __init__py
│ │ │ └── painы ответов API
│ │ ├── services/ # Бизнес-логика
│ │ │ ├── __init__.py
│ │ │ ├── nlp_service.py # NLP обработка
│ │ │ ├── vk_parser.py # Парсер VK
│ │ │ ├── telegram_parser.py # Парсер Telegram
│ │ │ └── pikabu_parser.py # Парсер Pikabu
│ │ ├── api/ # API роутеры
│ │ │ ├── __init__.py
│ │ │ └── pain_detector.py # Основные API endpoints
│ │ └── utils/ # Вспомогательные функции
│ │ ├── __init__.py
│ │ └── helpers.py
│ ├── data/ # SQLite файл БД
│ ├── requirements.txt # Python зависимости
│ ├── Dockerfile # Docker контейнер
│ └── .env # Переменные окружения
├── docker-compose.yml # Оркестрация контейнеров
├── nginx.conf # Конфигурация веб-сервера
└── README.md
```
