# from datetime import datetime
# from uuid import UUID, uuid4
# from sqlmodel import SQLModel, Field

# class BoardElement(SQLModel, table=True):
#     id: int | None = Field(default=None, primary_key=True)
#     room_id: UUID = Field(foreign_key="room.id")
#     author_id: int = Field(foreign_key="user.id")
#     element_type: str
#     data: str
#     created_at: datetime
#     updated_at: datetime | None = None
#     is_deleted: bool

from typing import TYPE_CHECKING
from uuid import UUID

from sqlmodel import Field, Relationship, SQLModel

from .base import BaseModel

if TYPE_CHECKING:
    from .board_element_comment import BoardElementComment
    from .room import Room
    from .user import User


class BoardElementBase(SQLModel):
    element_type: str
    data: str
    is_deleted: bool = False


class BoardElementPublic(BaseModel, BoardElementBase):
    id: int
    room_id: UUID
    author_id: int


class BoardElementCreate(BoardElementBase):
    room_id: UUID
    author_id: int


class BoardElementUpdate(BoardElementBase):
    element_type: str | None = None
    data: str | None = None
    is_deleted: bool | None = None


class BoardElement(BoardElementPublic, table=True):
    __tablename__ = 'board_element'
    id: int | None = Field(default=None, primary_key=True)
    room_id: UUID = Field(foreign_key='room.id')
    author_id: int = Field(foreign_key='user.id')

    room: 'Room' = Relationship(back_populates='board_elements')
    author: 'User' = Relationship(back_populates='board_elements')
    comments: list['BoardElementComment'] = Relationship(back_populates='board_element')
