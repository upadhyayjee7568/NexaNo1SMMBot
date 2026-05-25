from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env.production", extra="ignore")

    app_name: str = Field(default="Nexa SMM Panel", alias="APP_NAME")
    project_name: str = Field(default="Nexa Media Solution", alias="PROJECT_NAME")
    environment: str = Field(default="production", alias="ENVIRONMENT")
    timezone: str = Field(default="Asia/Kolkata", alias="TIMEZONE")

    telegram_bot_username: str = Field(default="NexaNo1SMMBot", alias="TELEGRAM_BOT_USERNAME")
    telegram_support_username: str = Field(default="NexaNo1Support", alias="TELEGRAM_SUPPORT_USERNAME")

    payment_gateway: str = Field(default="cashfree", alias="PAYMENT_GATEWAY")
    cashfree_mode: str = Field(default="LIVE", alias="CASHFREE_MODE")

    database_url: str = Field(default="postgresql://nexa:nexa_change_me@postgres:5432/nexa_smm", alias="DATABASE_URL")
    redis_url: str = Field(default="redis://redis:6379/0", alias="REDIS_URL")


settings = Settings()
