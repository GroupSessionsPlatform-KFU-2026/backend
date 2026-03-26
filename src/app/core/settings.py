from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    db_schema: str = 'postgresql+asyncpg'
    db_host: str = 'localhost'
    db_user: str = 'postgres'
    db_password: str = 'pass'
    db_port: int = 5432
    db_name: str = 'db'

    model_config = SettingsConfigDict(env_file='.env')


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
