from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP
from sqlmodel import Field, Relationship, SQLModel

from .base import BaseModel

if TYPE_CHECKING:
    from .project_tag import ProjectTag
    from .room import Room
    from .user import User


class ProjectBase(SQLModel):
    title: str
    description: str | None = None
    deadline: datetime | None = Field(
        default=None,
        sa_type=TIMESTAMP(timezone=True),
    )
    required_roles: list[str] = Field(
        default_factory=list,
        sa_column=Column(JSONB, nullable=False),
    )


class ProjectPublic(BaseModel, ProjectBase):
    owner_id: UUID
    is_archived: bool = False


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(SQLModel):
    title: str | None = None
    description: str | None = None
    deadline: datetime | None = None
    required_roles: list[str] | None = None


class Project(ProjectPublic, table=True):
    __tablename__ = 'project'

    owner_id: UUID = Field(foreign_key='user.id', nullable=False)

    owner: 'User' = Relationship(back_populates='projects')
    tags: list['ProjectTag'] = Relationship(back_populates='project')
    rooms: list['Room'] = Relationship(back_populates='project')
