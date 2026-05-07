from uuid import UUID

from sqlmodel import Field, SQLModel


class RolePermissionLink(SQLModel, table=True):
    __tablename__ = 'role_permission'
    role_id: UUID = Field(foreign_key='role.id', primary_key=True)
    permission_id: UUID = Field(foreign_key='permission.id', primary_key=True)
