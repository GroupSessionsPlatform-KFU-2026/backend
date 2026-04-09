from typing import TYPE_CHECKING
from uuid import UUID

from sqlmodel import Field, Relationship, SQLModel

from .base import BaseModel

if TYPE_CHECKING:
    from .project import Project
    from .tag import Tag


class ProjectTagBase(SQLModel):
    project_id: UUID
    tag_id: UUID


class ProjectTagPublic(BaseModel, ProjectTagBase):
    is_active: bool


class ProjectTagCreate(ProjectTagBase):
    pass


class ProjectTagUpdate(ProjectTagBase):
    pass


class ProjectTag(ProjectTagPublic, table=True):
    __tablename__ = 'project_tag'

    project_id: UUID = Field(foreign_key='project.id', nullable=False)
    tag_id: UUID = Field(foreign_key='tag.id', nullable=False)

    project: 'Project' = Relationship(back_populates='tags')
    tag: 'Tag' = Relationship(back_populates='project_tags')
