from typing import TYPE_CHECKING
from uuid import UUID

from sqlmodel import Field, Relationship, SQLModel

from .base import BaseModel

if TYPE_CHECKING:
    from .project_tag import ProjectTag
    from .room import Room
    from .user import User


class ProjectBase(SQLModel):
    title: str
    description: str | None = None


class ProjectPublic(BaseModel, ProjectBase):
    owner_id: UUID
    is_archived: bool = False


class ProjectCreate(ProjectBase):
    owner_id: UUID


class ProjectUpdate(ProjectBase):
    pass


class Project(ProjectPublic, table=True):
    __tablename__ = 'project'

    owner_id: UUID = Field(foreign_key='user.id', nullable=False)

    owner: 'User' = Relationship(back_populates='projects')
    tags: list['ProjectTag'] = Relationship(back_populates='project')
    rooms: list['Room'] = Relationship(back_populates='project')
