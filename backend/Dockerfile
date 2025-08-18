FROM python:3.11-slim

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    # Chromium + необходимые библиотеки для headless запуска
    chromium \
    chromium-driver \
    fonts-liberation \
    libnss3 \
    libgbm1 \
    libx11-6 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libasound2 \
    libatk-bridge2.0-0 \
    libxshmfence1 \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# Рабочая директория
WORKDIR /app

# Копирование и установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Установка SpaCy модели
RUN python -m spacy download ru_core_news_lg

# Копирование кода приложения
COPY . .

# Создание директории для БД
RUN mkdir -p /app/data

# Явно указываем путь к бинарнику Chromium (для кода, который читает CHROME_BINARY)
ENV CHROME_BINARY=/usr/bin/chromium

# Открытие порта
EXPOSE 8000

# Команда запуска
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
