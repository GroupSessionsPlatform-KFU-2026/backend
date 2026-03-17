# from datetime import datetime
# from sqlmodel import SQLModel, Field

# class BoardElementComment(SQLModel, table=True):
#     id: int | None = Field(default=None, primary_key=True)
#     board_element_id: int = Field(foreign_key="boardelement.id")
#     author_id: int = Field(foreign_key="user.id")
#     content: str
#     is_deleted: bool
#     created_at: datetime

from typing import TYPE_CHECKING
from uuid import UUID
from sqlmodel import Field, Relationship
from .base import Base

if TYPE_CHECKING:
    from .board_element import BoardElement
    from .user import User

class BoardElementCommentBase(Base):
    content: str
    is_deleted: bool = False

class BoardElementCommentPublic(BoardElementCommentBase):
    id: int
    board_element_id: int
    author_id: int

class BoardElementCommentCreate(BoardElementCommentBase):
    board_element_id: int
    author_id: int

class BoardElementCommentUpdate(BoardElementCommentBase):
    content: str | None = None
    is_deleted: bool | None = None

class BoardElementComment(BoardElementCommentPublic, table=True):
    __tablename__ = "boardelementcomment"
    id: int | None = Field(default=None, primary_key=True)
    board_element_id: int = Field(foreign_key="boardelement.id")
    author_id: int = Field(foreign_key="user.id")

    board_element: "BoardElement" = Relationship(back_populates="comments")
    author: "User" = Relationship(back_populates="comments")