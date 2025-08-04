from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite:///./pain_detector.db"
    
    class Config:
        env_file = ".env"


settings = Settings()