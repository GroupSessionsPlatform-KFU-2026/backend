# from datetime import datetime
# from sqlmodel import SQLModel, Field

# class Project(SQLModel, table=True):
#     id: int | None = Field(default=None, primary_key=True)
#     owner_id: int = Field(foreign_key="user.id")
#     title: str
#     description: str | None=None
#     created_at: datetime
#     updated_at: datetime | None = None
#     is_archived: bool

from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

from .base import BaseModel

if TYPE_CHECKING:
    from .project_tag import ProjectTag
    from .room import Room
    from .user import User


class ProjectBase(SQLModel):
    title: str
    description: str | None = None
    is_archived: bool = False


class ProjectPublic(BaseModel, ProjectBase):
    id: int
    owner_id: int


class ProjectCreate(ProjectBase):
    owner_id: int


class ProjectUpdate(ProjectBase):
    title: str | None = None
    description: str | None = None
    is_archived: bool | None = None


class Project(ProjectPublic, table=True):
    __tablename__ = 'project'
    id: int | None = Field(default=None, primary_key=True)
    owner_id: int = Field(foreign_key='user.id')

    owner: 'User' = Relationship(back_populates='projects')
    tags: list['ProjectTag'] = Relationship(back_populates='project')
    rooms: list['Room'] = Relationship(back_populates='project')
