from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env.production", extra="ignore")

    app_name: str = Field(default="Nexa SMM Panel", alias="APP_NAME")
    project_name: str = Field(default="Nexa Media Solution", alias="PROJECT_NAME")
    environment: str = Field(default="production", alias="ENVIRONMENT")
    timezone: str = Field(default="Asia/Kolkata", alias="TIMEZONE")

    telegram_bot_username: str = Field(default="NexaNo1SMMBot", alias="TELEGRAM_BOT_USERNAME")
    telegram_bot_token: str = Field(default="", alias="TELEGRAM_BOT_TOKEN")
    telegram_support_username: str = Field(default="NexaNo1Support", alias="TELEGRAM_SUPPORT_USERNAME")
    telegram_updates_channel: str = Field(default="https://t.me/NexaNo1Updates", alias="TELEGRAM_UPDATES_CHANNEL")
    telegram_discussion_group: str = Field(default="@NexaCommunity", alias="TELEGRAM_DISCUSSION_GROUP")
    telegram_force_join_enabled: bool = Field(default=True, alias="TELEGRAM_FORCE_JOIN_ENABLED")

    payment_gateway: str = Field(default="cashfree", alias="PAYMENT_GATEWAY")
    cashfree_mode: str = Field(default="LIVE", alias="CASHFREE_MODE")
    cashfree_webhook_secret: str = Field(default="", alias="CASHFREE_WEBHOOK_SECRET")
    min_add_money_inr: int = Field(default=100, alias="MIN_ADD_MONEY_INR")

    database_url: str = Field(default="postgresql://nexa:nexa_change_me@postgres:5432/nexa_smm", alias="DATABASE_URL")
    redis_url: str = Field(default="redis://redis:6379/0", alias="REDIS_URL")

    provider_1_base_url: str = Field(default="https://justanotherpanel.com/api/v2", alias="PROVIDER_1_BASE_URL")
    provider_1_api_key: str = Field(default="", alias="PROVIDER_1_API_KEY")
    provider_2_base_url: str = Field(default="https://peakerr.com/api/v2", alias="PROVIDER_2_BASE_URL")
    provider_2_api_key: str = Field(default="", alias="PROVIDER_2_API_KEY")
    provider_timeout_seconds: int = Field(default=20, alias="PROVIDER_TIMEOUT_SECONDS")

    web_session_cookie_name: str = Field(default="nexa_session", alias="WEB_SESSION_COOKIE_NAME")


settings = Settings()
