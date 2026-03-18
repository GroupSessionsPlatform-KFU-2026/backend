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
| DB_SCHEMA         | Протокол подключения к БД | Строка (драйвер)      | postgresql+asyncpg    |
| DB_HOST           | Хост БД                   | Строка                | localhost             |
| DB_PORT           | Порт БД                   | Число                 | 5432                  |
| DB_USER           | Имя пользователя в БД     | Строка                | postgres              |
| DB_PASSWORD       | Пароль БД                 | Строка                | pass                  |
| DB_NAME           | Название БД               | Строка                | db                    |
| DEBUG             | Режим отладки             | Логический тип (bool) | -                     |
| BASE_URL          | Базовый URL backend       | Строка                | —                     |
| BASE_URL_FRONTEND | Базовый URL frontend      | Строка                | —                     |
| SMTP_SERVER       | Хост SMTP-сервера         | Строка                | —                     |
| SMTP_PORT         | Порт SMTP-сервера         | Число                 | —                     |
| SMTP_USER         | Имя пользователя SMTP     | Строка                | —                     |
| SMTP_PASSWORD     | Пароль SMTP               | Строка                | —                     |
| JWT_SECRET        | Секретный ключ для JWT    | Строка                | —                     |
| JWT_ALGORITHM     | Алгоритм подписи JWT      | Строка                | -                     |
| JWT_TIME_EXP      | Время жизни JWT (секунды) | Число                 | -                     |


---

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