from functools import lru_cache

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class AuthSettings(BaseModel):
    secret: str = 'secret'
    access_token_lifetime_seconds: int = 300
    refresh_token_lifetime_seconds: int = 600
    token_algorithm: str = 'HS256'


class DBSettings(BaseModel):
    db_schema: str = 'postgresql+asyncpg'
    db_host: str = 'localhost'
    db_user: str = 'postgres'
    db_password: str = 'pass'
    db_port: int = 5432
    db_name: str = 'db'


class RBACSettings(BaseModel):
    admin_email: str = 'admin@example.com'
    admin_password: str = 'admin123456'
    admin_role: str = 'admin'
    public_role: str = 'public'


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env',
        env_nested_delimiter='__',
        extra='ignore',
    )

    db: DBSettings = DBSettings()
    auth: AuthSettings = AuthSettings()
    rbac: RBACSettings = RBACSettings()


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
