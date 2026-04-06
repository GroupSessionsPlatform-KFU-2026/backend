from sqlalchemy.engine import URL
from sqlalchemy.ext.asyncio import create_async_engine

from src.app.core.settings import settings


def form_db_url() -> str:
    return URL.create(
        drivername=settings.db.db_schema,
        username=settings.db.db_user,
        password=settings.db.db_password,
        host=settings.db.db_host,
        port=settings.db.db_port,
        database=settings.db.db_name,
    ).render_as_string(hide_password=False)


engine = create_async_engine(form_db_url())
