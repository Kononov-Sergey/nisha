#!/bin/bash

echo "🚀 Запуск в режиме разработки"
echo "================================"

# Запуск бэкенда в Docker
echo "📦 Запускаем бэкенд в Docker..."
docker-compose -f docker-compose.dev.yml up -d

# Ждем запуска бэкенда
echo "⏳ Ждем запуска бэкенда..."

# Проверяем что бэкенд запустился
echo "🔍 Проверяем бэкенд..."
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ Бэкенд запущен успешно (http://localhost:8000)"
    echo "📖 Swagger UI: http://localhost:8000/docs"
else
    echo "❌ Ошибка запуска бэкенда"
    exit 1
fi