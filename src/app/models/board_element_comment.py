from typing import TYPE_CHECKING
from uuid import UUID

from sqlmodel import Relationship, SQLModel

from .base import BaseModel

if TYPE_CHECKING:
    from .board_element import BoardElement
    from .user import User


class BoardElementCommentBase(SQLModel):
    content: str


class BoardElementCommentPublic(BaseModel, BoardElementCommentBase):
    board_element_id: UUID
    author_id: UUID
    is_deleted: bool


class BoardElementCommentCreate(BoardElementCommentBase):
    board_element_id: UUID
    author_id: UUID


class BoardElementCommentUpdate(BoardElementCommentBase):
    pass


class BoardElementComment(BoardElementCommentPublic, table=True):
    __tablename__ = 'board_element_comment'

    board_element: 'BoardElement' = Relationship(back_populates='comments')
    author: 'User' = Relationship(back_populates='comments')
