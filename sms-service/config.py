from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    sqs_endpoint_url: str | None = None
    sms_queue_name: str = "sms-notifications"
    aws_region: str = "us-east-1"
    api_url: str
    internal_api_key: SecretStr


settings = Settings.model_validate({})
