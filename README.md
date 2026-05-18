# Group Sessions Platform — Backend

Пример backend-сервиса на FastAPI для платформы совместных учебных сессий.

Система позволяет:
- Создавать учебные сессии
- Взаимодействовать в реальном времени (WebSocket)
- Общаться через чат
- Использовать таймер Pomodoro

## Роли
- Модератор — создаёт и управляет сессией  
- Участник — подключается и взаимодействует  

## Стек технологий
- FastAPI  
- SQLAlchemy / SQLModel  
- Alembic (миграции БД)  
- PostgreSQL (asyncpg, psycopg)   
- uv (менеджер пакетов)  
- ruff (линтер и форматтер)  
- pre-commit  

---

## Команда разработки
- @khazmalika — backend  
- @xludw1ng — backend  

---

# Переменные среды
Перед запуском необходимо указать переменные среды  
Шаблон файла переменных среды - `.env.example`  
Переменные среды должны быть указаны в `.env`

| Название | Описание | Значение по умолчанию |
| --- | --- | --- |
| DB__DRIVER | Драйвер подключения к БД | postgresql+asyncpg |
| DB__HOST | Хост БД | localhost |
| DB__PORT | Порт БД | 5432 |
| DB__USER | Пользователь БД | postgres |
| DB__PASSWORD | Пароль БД | pass |
| DB__NAME | Имя БД | db |
| AUTH__SECRET | Секрет для создания JWT-токенов | secret |
| AUTH__TOKEN_ALGORITHM | Алгоритм JWT | HS256 |
| AUTH__ACCESS_TOKEN_LIFETIME_SECONDS | Время жизни access-токена | 300 |
| AUTH__REFRESH_TOKEN_LIFETIME_SECONDS | Время жизни refresh-токена | 600 |
| AUTH__COOKIE_SECURE | Secure-флаг refresh-cookie | false |
| RBAC__ADMIN_EMAIL | Email admin-пользователя | admin@example.com |
| RBAC__ADMIN_PASSWORD | Пароль admin-пользователя | admin |
| RBAC__ADMIN_ROLE | Название admin-роли | admin |
| RBAC__PUBLIC_ROLE | Название роли для новых пользователей | public |
| SOCKET__PATH | Path для Socket.IO | socket.io |
| SOCKET__CORS_ALLOWED_ORIGINS | Разрешенные origins для Socket.IO | * |
| COMMON__SCHEME | Схема внешнего адреса | http |
| COMMON__HOST | Хост внешнего адреса | localhost |
| COMMON__BACKEND_PORT | Порт backend без reverse-proxy | 8000 |
| COMMON__FRONTEND_PORT | Порт frontend | 5173 |
| RATE_LIMIT__DEFAULT | Общий rate limit | 100/minute |
| RATE_LIMIT__AUTH | Rate limit auth-роутов | 10/minute |
| EMAIL__USERNAME | SMTP username | example@gmail.com |
| EMAIL__PASSWORD | SMTP password |  |
| EMAIL__SERVER | SMTP server | smtp.gmail.com |
| EMAIL__PORT | SMTP port | 587 |
| EMAIL__FROM_EMAIL | Email отправителя | example@gmail.com |
| EMAIL__FROM_NAME | Имя отправителя | Example |
| EMAIL__STARTTLS | Использовать STARTTLS | true |
| EMAIL__SSL_TLS | Использовать SSL/TLS | false |
| EMAIL__USE_CREDENTIALS | Использовать SMTP credentials | true |
| EMAIL__VALIDATE_CERTS | Проверять сертификаты | true |
| EMAIL__NOTIFICATION_LIFETIME_SECONDS | Время жизни email-кода | 3600 |
| EMAIL__TEMPLATE_FOLDER | Папка email-шаблонов | src/app/templates |

---
Для генерации AUTH_SECRET можно использовать openssl
```bash
openssl rand -hex 32
```

# Инструкции по запуску
## Пререквизиты
- Установлен python
- Установлен uv

## Подготовка к запуску
### Установка зависимостей
```bash
uv sync
```

### Запуск миграций
```bash
uv run alembic upgrade head
```

## Запуск проекта
```bash
uv run fastapi dev
```

## Команды для разработки
### Генерация миграций
```bash
uv run alembic revision --autogenerate -m "<коментарий>"
```

### Установка pre-commit
```bash
uv run pre-commit install
```

## Запуск через Docker Compose

### Подготовка

Скопировать `.env.example` в `.env`

Linux/macOS:

```bash
cp .env.example .env
```

Windows:

```powershell
copy .env.example .env
```

При необходимости изменить значения переменных в `.env`

Образ backend должен быть опубликован в DockerHub как `xludw1ng/studiom-backend:latest`.

Для публикации новой версии backend-образа:

```bash
docker login
docker build -t xludw1ng/studiom-backend:latest .
docker push xludw1ng/studiom-backend:latest
```

### Запуск проекта

```bash
docker compose up
```

### Доступ к сервисам

| Сервис      | Адрес                       |
|-------------|-----------------------------|
| API         | http://localhost/api/v1     |
| Swagger     | http://localhost/docs       |
| OpenAPI     | http://localhost/openapi.json |
| Healthcheck | http://localhost/health     |
| Socket.IO   | http://localhost/socket.io  |

### Остановка контейнеров

```bash
docker compose down
```
