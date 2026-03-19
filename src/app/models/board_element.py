from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, Relationship, SQLModel

from .base import BaseModel

if TYPE_CHECKING:
    from .board_element_comment import BoardElementComment
    from .room import Room
    from .user import User


class BoardElementBase(SQLModel):
    element_type: str
    data: dict[str, Any] = Field(sa_column=Column(JSONB, nullable=False))


class BoardElementPublic(BaseModel, BoardElementBase):
    room_id: UUID
    author_id: UUID
    is_deleted: bool


class BoardElementCreate(BoardElementBase):
    room_id: UUID
    author_id: UUID


class BoardElementUpdate(BoardElementBase):
    pass


class BoardElement(BoardElementPublic, table=True):
    __tablename__ = 'board_element'

    room: 'Room' = Relationship(back_populates='board_elements')
    author: 'User' = Relationship(back_populates='board_elements')
    comments: list['BoardElementComment'] = Relationship(back_populates='board_element')
