FROM python:3.12-slim-bookworm AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0

COPY pyproject.toml uv.lock ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project


FROM python:3.12-slim-bookworm AS starter

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && adduser --disabled-password --gecos "" --uid 1000 appuser \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/.venv /app/.venv

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH="/app"

COPY __init__.py ./src/__init__.py
COPY app ./src/app
COPY alembic.ini ./alembic.ini
COPY migrations ./migrations

RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

CMD ["gunicorn", "-c", "src/app/gunicorn_config.py", "src.app.main:app"]
