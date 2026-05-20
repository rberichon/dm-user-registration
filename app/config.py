from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8"
    )

    database_url: str = "postgresql://localhost/app"
    mail_service_url: str = "http://localhost:8025"


settings = Settings()
