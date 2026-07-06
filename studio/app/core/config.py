from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = Field(default="local", alias="APP_ENV")
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8080, alias="API_PORT")

    database_url: str = Field(default="sqlite:///./olivewolf_studio.db", alias="DATABASE_URL")
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    object_store_root: str = Field(default="./storage", alias="OBJECT_STORE_ROOT")
    studio_api_key: str | None = Field(default=None, alias="STUDIO_API_KEY")
    max_upload_mb: int = Field(default=25, alias="MAX_UPLOAD_MB")

    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    elevenlabs_api_key: str | None = Field(default=None, alias="ELEVENLABS_API_KEY")

    cors_origins_raw: str = Field(default="http://localhost:3000,http://localhost:8080", alias="CORS_ORIGINS")

    @property
    def cors_origins(self) -> list[str]:
        return [x.strip() for x in self.cors_origins_raw.split(",") if x.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
