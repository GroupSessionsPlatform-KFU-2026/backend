from typing import TYPE_CHECKING

from sqlalchemy import UniqueConstraint
from sqlmodel import Relationship, SQLModel

from .base import BaseModel
from .role_permission import RolePermissionLink

if TYPE_CHECKING:
    from .role import Role


class PermissionBase(SQLModel):
    subject: str
    action: str


class PermissionPublic(BaseModel, PermissionBase):
    pass


class Permission(PermissionPublic, table=True):
    __tablename__ = 'permission'
    __table_args__ = (
        UniqueConstraint('subject', 'action', name='uq_permission_subject_action'),
    )

    roles: list['Role'] = Relationship(
        back_populates='permissions',
        link_model=RolePermissionLink,
    )

    @property
    def scope(self) -> str:
        return f'{self.subject}:{self.action}'
