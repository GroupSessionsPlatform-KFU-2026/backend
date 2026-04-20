from typing import TYPE_CHECKING

from sqlalchemy import UniqueConstraint
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
    __table_args__ = (UniqueConstraint('name', name='uq_tag_name'),)

    project_tags: list['ProjectTag'] = Relationship(back_populates='tag')
