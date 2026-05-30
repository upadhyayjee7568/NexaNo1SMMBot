from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env.production", extra="ignore")

    app_name: str = Field(default="Nexa SMM Panel", alias="APP_NAME")
    project_name: str = Field(default="Nexa Media Solution", alias="PROJECT_NAME")
    environment: str = Field(default="production", alias="ENVIRONMENT")
    timezone: str = Field(default="Asia/Kolkata", alias="TIMEZONE")

    # Public base URL of the deployment (used for Cashfree return/notify URLs and Telegram webhook).
    public_base_url: str = Field(default="", alias="PUBLIC_BASE_URL")

    telegram_bot_username: str = Field(default="NexaNo1SMMBot", alias="TELEGRAM_BOT_USERNAME")
    telegram_bot_token: str = Field(default="", alias="TELEGRAM_BOT_TOKEN")
    telegram_support_username: str = Field(default="NexaNo1Support", alias="TELEGRAM_SUPPORT_USERNAME")
    telegram_updates_channel: str = Field(default="https://t.me/NexaNo1Updates", alias="TELEGRAM_UPDATES_CHANNEL")
    telegram_discussion_group: str = Field(default="@NexaCommunity", alias="TELEGRAM_DISCUSSION_GROUP")
    telegram_force_join_enabled: bool = Field(default=True, alias="TELEGRAM_FORCE_JOIN_ENABLED")
    # Secret token Telegram echoes back in the X-Telegram-Bot-Api-Secret-Token header to authenticate webhooks.
    telegram_webhook_secret: str = Field(default="", alias="TELEGRAM_WEBHOOK_SECRET")

    # Admin / ownership
    admin_telegram_id: int = Field(default=0, alias="ADMIN_TELEGRAM_ID")
    admin_username: str = Field(default="NexaNo1Support", alias="ADMIN_USERNAME")
    admin_2fa_enabled: bool = Field(default=False, alias="ADMIN_2FA_ENABLED")
    admin_2fa_code: str = Field(default="", alias="ADMIN_2FA_CODE")

    # Payments
    payment_gateway: str = Field(default="cashfree", alias="PAYMENT_GATEWAY")
    cashfree_mode: str = Field(default="LIVE", alias="CASHFREE_MODE")
    cashfree_app_id: str = Field(default="", alias="CASHFREE_APP_ID")
    cashfree_secret_key: str = Field(default="", alias="CASHFREE_SECRET_KEY")
    cashfree_webhook_secret: str = Field(default="", alias="CASHFREE_WEBHOOK_SECRET")
    min_add_money_inr: int = Field(default=100, alias="MIN_ADD_MONEY_INR")
    max_add_money_inr: int = Field(default=100000, alias="MAX_ADD_MONEY_INR")

    # UPI fallback (used automatically when Cashfree is unavailable / disabled)
    upi_fallback_enabled: bool = Field(default=True, alias="UPI_FALLBACK_ENABLED")
    admin_upi_id: str = Field(default="", alias="ADMIN_UPI_ID")
    upi_payee_name: str = Field(default="Nexa Media Solution", alias="UPI_PAYEE_NAME")
    # Auto-credit cap: UPI top-ups at or below this amount are auto-credited on UTR submit;
    # larger amounts are held as 'pending' for admin review (fraud mitigation).
    upi_auto_credit_max_inr: int = Field(default=5000, alias="UPI_AUTO_CREDIT_MAX_INR")

    database_url: str = Field(default="postgresql://nexa:nexa_change_me@postgres:5432/nexa_smm", alias="DATABASE_URL")
    redis_url: str = Field(default="", alias="REDIS_URL")

    provider_1_name: str = Field(default="JustAnotherPanel", alias="PROVIDER_1_NAME")
    provider_1_base_url: str = Field(default="https://justanotherpanel.com/api/v2", alias="PROVIDER_1_BASE_URL")
    provider_1_api_key: str = Field(default="", alias="PROVIDER_1_API_KEY")
    provider_2_name: str = Field(default="Peakerr API", alias="PROVIDER_2_NAME")
    provider_2_base_url: str = Field(default="https://peakerr.com/api/v2", alias="PROVIDER_2_BASE_URL")
    provider_2_api_key: str = Field(default="", alias="PROVIDER_2_API_KEY")
    provider_timeout_seconds: int = Field(default=20, alias="PROVIDER_TIMEOUT_SECONDS")

    web_session_cookie_name: str = Field(default="nexa_session", alias="WEB_SESSION_COOKIE_NAME")


settings = Settings()
