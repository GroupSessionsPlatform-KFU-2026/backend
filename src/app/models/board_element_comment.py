from typing import TYPE_CHECKING
from uuid import UUID

from sqlmodel import Field, Relationship, SQLModel

from .base import BaseModel

if TYPE_CHECKING:
    from .board_element import BoardElement
    from .user import User


class BoardElementCommentBase(SQLModel):
    content: str
    is_anonymous: bool = Field(default=False, nullable=False)


class BoardElementCommentPublic(BaseModel, BoardElementCommentBase):
    board_element_id: UUID
    author_id: UUID | None = None
    is_deleted: bool


class BoardElementCommentCreate(BoardElementCommentBase):
    board_element_id: UUID | None = None
    author_id: UUID | None = None


class BoardElementCommentUpdate(BoardElementCommentBase):
    pass


class BoardElementComment(BoardElementCommentPublic, table=True):
    __tablename__ = 'board_element_comment'

    board_element_id: UUID = Field(foreign_key='board_element.id', nullable=False)
    author_id: UUID = Field(foreign_key='user.id', nullable=False)

    board_element: 'BoardElement' = Relationship(back_populates='comments')
    author: 'User' = Relationship(back_populates='comments')
