from functools import lru_cache

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class AuthSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix='AUTH_',
    )
    secret: str = 'secret'
    access_token_lifetime_seconds: int = 300
    refresh_token_lifetime_seconds: int = 600
    token_algorithm: str = 'HS256'
    cookie_secure: bool = False


class DBSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env',
        extra='ignore',
    )

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


class SocketSettings(BaseModel):
    cors_allowed_origins: str | list[str] = '*'
    path: str = 'socket.io'


class CommonSettings(BaseModel):
    host: str = 'http://localhost:8000'
    frontend_host: str = 'http://localhost:5173'
    cors_allowed_origins: list[str] = [
        'http://localhost:5173',
        'http://localhost:3000',
        'http://localhost:8080',
    ]
    cors_allowed_methods: list[str] = [
        'GET',
        'POST',
        'PUT',
        'PATCH',
        'DELETE',
        'OPTIONS',
    ]
    cors_allowed_headers: list[str] = [
        'Authorization',
        'Content-Type',
        'Accept',
    ]


class RateLimitSettings(BaseModel):
    default: str = '100/minute'
    auth: str = '10/minute'


class EmailSettings(BaseModel):
    username: str = 'studiom.backend@gmail.com'
    password: str = ''
    server: str = 'smtp.gmail.com'
    port: int = 587
    from_email: str = 'studiom.backend@gmail.com'
    from_name: str = 'Studiom'
    starttls: bool = True
    ssl_tls: bool = False
    use_credentials: bool = True
    validate_certs: bool = True
    notification_lifetime_seconds: int = 3600
    app_base_url: str = 'http://localhost:5173'
    template_folder: str = 'src/app/templates'


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env',
        env_nested_delimiter='__',
        extra='ignore',
    )

    db: DBSettings = DBSettings()
    auth: AuthSettings = AuthSettings()
    rbac: RBACSettings = RBACSettings()
    socket: SocketSettings = SocketSettings()
    email: EmailSettings = EmailSettings()
    common: CommonSettings = CommonSettings()
    rate_limit: RateLimitSettings = RateLimitSettings()



@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()