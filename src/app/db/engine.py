from sqlalchemy.engine import URL
from sqlalchemy.ext.asyncio import create_async_engine

from src.app.core.settings import settings


def form_db_url() -> str:
    return URL.create(
        drivername=settings.db.driver,
        username=settings.db.user,
        password=settings.db.password,
        host=settings.db.host,
        port=settings.db.port,
        database=settings.db.name,
    ).render_as_string(hide_password=False)


engine = create_async_engine(form_db_url())
