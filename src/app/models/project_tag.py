# from datetime import datetime
# from sqlmodel import SQLModel, Field

# class ProjectTag(SQLModel, table=True):
#     id: int | None = Field(default=None, primary_key=True)
#     project_id: int = Field(foreign_key="project.id")
#     tag_id: int = Field(foreign_key="tag.id")
#     created_at: datetime
#     is_active: bool

from typing import TYPE_CHECKING
from sqlmodel import Field, Relationship
from .base import Base

if TYPE_CHECKING:
    from .project import Project
    from .tag import Tag

class ProjectTagBase(Base):
    is_active: bool = True

class ProjectTagPublic(ProjectTagBase):
    id: int

class ProjectTagCreate(ProjectTagBase):
    project_id: int
    tag_id: int

class ProjectTagUpdate(ProjectTagBase):
    is_active: bool | None = None

class ProjectTag(ProjectTagPublic, table=True):
    __tablename__ = "projecttag"
    id: int | None = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="project.id")
    tag_id: int = Field(foreign_key="tag.id")

    project: "Project" = Relationship(back_populates="tags")
    tag: "Tag" = Relationship(back_populates="project_tags")