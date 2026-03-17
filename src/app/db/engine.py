from sqlalchemy.engine import URL
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.settings import settings


def form_db_url() -> str:
    return URL.create(
        drivername=settings.db_schema,
        username=settings.db_user,
        password=settings.db_password,
        host=settings.db_host,
        port=settings.db_port,
        database=settings.db_name,
    ).render_as_string(hide_password=False)


engine = create_async_engine(form_db_url())
