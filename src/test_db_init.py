import asyncio
import sys

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from src.app.db.engine import form_test_db_url
from src.app.init import init_rbac


async def init_test_db(session_maker: async_sessionmaker[AsyncSession]) -> None:
    engine = session_maker.kw['bind']

    async with engine.begin() as connection:
        await connection.run_sync(SQLModel.metadata.create_all)

    async with session_maker() as session:
        await init_rbac(session)


async def drop_test_db(session_maker: async_sessionmaker[AsyncSession]) -> None:
    engine = session_maker.kw['bind']

    async with engine.begin() as connection:
        await connection.run_sync(SQLModel.metadata.drop_all)


async def init_local_test_db(db_path: str = 'db.sqlite3') -> None:
    engine = create_async_engine(
        form_test_db_url(db_path),
        connect_args={'check_same_thread': False},
    )
    session_maker = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    await drop_test_db(session_maker)
    await init_test_db(session_maker)
    await engine.dispose()


if __name__ == '__main__':
    database_path = sys.argv[1] if len(sys.argv) > 1 else 'db.sqlite3'
    asyncio.run(init_local_test_db(database_path))
