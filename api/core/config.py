from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )

    database_url: str
    
    sms_service_url: str
    sms_service_timeout: float = 5.0

    secret_key: SecretStr
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    reset_token_expire_minutes: int = 60


settings = Settings.model_validate({})
