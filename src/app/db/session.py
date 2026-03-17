from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from app.core.settings import settings

# def form_db_url() -> str:
#     return settings.db_url

# engine = create_async_engine(form_db_url())

from app.db.engine import engine

async def get_session():
    async with AsyncSession(engine) as session:
        yield session

SessionDep = Annotated[AsyncSession, Depends(get_session)]