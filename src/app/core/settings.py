from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AuthSettings(BaseSettings):
    secret: str = 'secret'
    access_token_lifetime_seconds: int = 300
    refresh_token_lifetime_seconds: int = 600
    token_algorithm: str = 'HS256'
    cookie_secure: bool = False


class DBSettings(BaseSettings):
    driver: str = 'postgresql+asyncpg'
    host: str = 'localhost'
    user: str = 'postgres'
    password: str = 'pass'
    port: int = 5432
    name: str = 'db'


class PomodoroDefaultsSettings(BaseSettings):
    work_duration: int = Field(default=25, gt=0)
    short_break_duration: int = Field(default=5, gt=0)
    long_break_duration: int = Field(default=15, gt=0)
    cycles_before_long: int = Field(default=4, gt=0)


class RBACSettings(BaseSettings):
    admin_email: str = 'admin@example.com'
    admin_password: str = 'admin123456'
    admin_role: str = 'admin'
    public_role: str = 'public'


class SocketSettings(BaseSettings):
    cors_allowed_origins: str | list[str] = '*'
    path: str = 'socket.io'


class CommonSettings(BaseSettings):
    scheme: str = 'http'
    host: str = 'localhost'
    backend_port: int = 8000
    frontend_port: int = 5173
    cors_allowed_origins: list[str] = [
        'http://localhost',
        'http://localhost:80',
        'http://localhost:3000',
        'http://localhost:5173',
        'http://localhost:8000',
        'http://localhost:8080',
        'http://127.0.0.1:8000',
        'http://0.0.0.0:8000',
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

    @property
    def backend_host(self) -> str:
        return f'{self.scheme}://{self.host}:{self.backend_port}'

    @property
    def frontend_host(self) -> str:
        return f'{self.scheme}://{self.host}:{self.frontend_port}'


class RateLimitSettings(BaseSettings):
    default: str = '100/minute'
    auth: str = '10/minute'


class EmailSettings(BaseSettings):
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
    pomodoro: PomodoroDefaultsSettings = PomodoroDefaultsSettings()


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
