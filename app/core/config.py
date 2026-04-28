from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "smart-recommendation-api"
    APP_ENV: str = "development"
    DEBUG: bool = True

    DATABASE_URL: str

    SECRET_KEY: str = "change-me-in-production"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
