from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "smart-recommendation-api"
    APP_ENV: str = "development"
    DEBUG: bool = True

    DATABASE_URL: str

    SECRET_KEY: str = "change-me-in-production"

    MODEL_DIR: str = "models"

    # Background jobs
    # Set to 0 to disable automatic retraining (manual trigger still available)
    RETRAIN_INTERVAL_HOURS: int = 6

    # CORS
    # Comma-separated list of allowed origins.
    # Default covers Angular dev server (ng serve) and a local API client.
    # In production, set this to the deployed frontend URL.
    ALLOWED_ORIGINS: str = "http://localhost:4200,http://localhost:3000"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
