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

| Название          | Описание                  | Тип                   | Значение по умолчанию |
| ----------------- | ------------------------- | --------------------- |-----------------------|
| DB__DRIVER          | Протокол подключения к БД | Строка (драйвер)      | postgresql+asyncpg    |
| DB__HOST           | Хост БД                   | Строка                | localhost             |
| DB__PORT           | Порт БД                   | Число                 | 5432                  |
| DB__USER           | Имя пользователя в БД     | Строка                | postgres              |
| DB__PASSWORD       | Пароль БД                 | Строка                | pass                  |
| DB__NAME           | Название БД               | Строка                | db                    |
| AUTH_SECRET | Секрет для создания JWT-токенов | Строка | secret |
| AUTH_ACCESS_TOKEN_LIFETIME_SECONDS | Время жизни access-токенов в секундах | Число | 300 |
| AUTH_REFRESH_TOKEN_LIFETIME_SECONDS | Время жизни refresh-токенов в секундах | Число | 600 |
| AUTH_TOKEN_ALGORITHM | Алгоритм шифрования JWT-токенов | Строка | HS256 |

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

## Run database

```bash
docker compose up -d
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

### Запуск проекта

```bash
docker compose up
```

### Доступ к сервисам

| Сервис      | Адрес                       |
|-------------|-----------------------------|
| API         | http://localhost/api        |
| Swagger     | http://localhost/docs       |
| Healthcheck | http://localhost/api/health |

### Остановка контейнеров

```bash
docker compose down
```
