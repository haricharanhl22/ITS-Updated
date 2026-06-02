from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "HCAI-ITS"
    debug: bool = False

    # JWT settings
    secret_key: str = "supersecretjwtkey_change_this_in_production_32chars"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # Supabase settings
    supabase_url: str = ""
    supabase_key: str = ""

    # Resend email settings
    resend_api_key: str = ""

    # SMTP settings (e.g. Gmail, Brevo SMTP)
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from_email: str = ""
    smtp_from_name: str = "HCAI-ITS Support"


settings = Settings()
