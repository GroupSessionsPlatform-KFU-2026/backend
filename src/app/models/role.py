from typing import TYPE_CHECKING

from sqlalchemy import UniqueConstraint
from sqlmodel import Relationship, SQLModel

from .base import BaseModel
from .role_permission import RolePermissionLink
from .user_role import UserRoleLink

if TYPE_CHECKING:
    from .permission import Permission
    from .user import User


class RoleBase(SQLModel):
    name: str


class RolePublic(BaseModel, RoleBase):
    pass


class Role(RolePublic, table=True):
    __tablename__ = 'role'
    __table_args__ = (UniqueConstraint('name', name='uq_role_name'),)

    users: list['User'] = Relationship(
        back_populates='roles',
        link_model=UserRoleLink,
    )
    permissions: list['Permission'] = Relationship(
        back_populates='roles',
        link_model=RolePermissionLink,
    )