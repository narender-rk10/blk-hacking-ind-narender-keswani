"""Application configuration and environment variables."""

import os


class Settings:
    APP_NAME: str = "BlackRock Auto-Savings API"
    APP_VERSION: str = "1.0.0"
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "5477"))
    WORKERS: int = int(os.getenv("WORKERS", "4"))
    ENV: str = os.getenv("ENV", "development")

    # NPS constants
    NPS_RATE: float = 0.0711
    NPS_MAX_DEDUCTION: float = 200000.0
    NPS_INCOME_PERCENT: float = 0.10

    # Index Fund constants
    INDEX_RATE: float = 0.1449

    # Retirement age
    RETIREMENT_AGE: int = 60
    MIN_INVESTMENT_YEARS: int = 5

    # Ceiling multiple
    CEILING_MULTIPLE: int = 100

    # Date format
    DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"


settings = Settings()
