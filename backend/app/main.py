from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.core.config import settings
from app.core.database import engine, Base
from app.api import pain_detector

# Создание таблиц в БД
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Pain Detector API",
    description="AI-сервис для поиска болей предпринимателей",
    version="1.0.0"
)

# CORS для фронтенда
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене укажите конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение роутеров
app.include_router(pain_detector.router, prefix="/api", tags=["pain-detection"])

# Статические файлы для фронтенда
app.mount("/", StaticFiles(directory="static", html=True), name="static")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
