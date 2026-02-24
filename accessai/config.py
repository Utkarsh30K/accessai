from pydantic_settings import BaseSettings
from typing import Dict


class Settings(BaseSettings):
    """
    Loads configuration from environment variables and .env file.
    """
    DATABASE_URL: str
    SECRET_KEY: str
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/auth/callback"
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    SENTRY_DSN: str = ""

    class Config:
        env_file = ".env"


# Credit packages configuration
CREDIT_PACKAGES: Dict = {
    "starter": {"credits": 200, "price_usd": 9},
    "pro": {"credits": 500, "price_usd": 19}
}


# Create a single, reusable instance of the settings
settings = Settings()
