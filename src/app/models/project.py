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

from sqlmodel import Relationship, SQLModel

from .base import BaseModel

if TYPE_CHECKING:
    from .project_tag import ProjectTag
    from .room import Room
    from .user import User


class ProjectBase(SQLModel):
    title: str
    description: str | None = None


class ProjectPublic(BaseModel, ProjectBase):
    owner_id: int
    is_archived: bool = False


class ProjectCreate(ProjectBase):
    owner_id: int


class ProjectUpdate(ProjectBase):
    pass


class Project(ProjectPublic, table=True):
    __tablename__ = 'project'

    owner: 'User' = Relationship(back_populates='projects')
    tags: list['ProjectTag'] = Relationship(back_populates='project')
    rooms: list['Room'] = Relationship(back_populates='project')
