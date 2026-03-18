# from datetime import datetime
# from sqlmodel import SQLModel, Field

# class Tag(SQLModel, table=True):
#     id: int | None = Field(default=None, primary_key=True)
#     name: str = Field(index=True)
#     color: str
#     description: str | None = None
#     created_at: datetime

from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

from .base import BaseModel

if TYPE_CHECKING:
    from .project_tag import ProjectTag


class TagBase(SQLModel):
    name: str = Field(index=True)
    color: str
    description: str | None = None


class TagPublic(BaseModel, TagBase):
    pass


class TagCreate(TagBase):
    pass


class TagUpdate(TagBase):
    pass


class Tag(TagPublic, table=True):
    __tablename__ = 'tag'

    project_tags: list['ProjectTag'] = Relationship(back_populates='tag')
