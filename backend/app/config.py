from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""
    supabase_jwt_secret: str = ""

    database_url: str = ""

    redis_url: str = "redis://localhost:6379"

    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_price_monthly: str = ""
    stripe_price_annual: str = ""

    environment: str = "development"
    frontend_url: str = "http://localhost:3000"

    sentry_dsn: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
