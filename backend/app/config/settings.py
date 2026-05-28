from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "HCAI-ITS"
    debug: bool = False

    # JWT settings
    secret_key: str = "supersecretjwtkey_change_this_in_production_32chars"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60


settings = Settings()
