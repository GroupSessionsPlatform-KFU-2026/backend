# from datetime import datetime
# from uuid import UUID, uuid4
# from sqlmodel import SQLModel, Field


# class ChatMessage(SQLModel, table=True):
#     id: int | None = Field(default=None, primary_key=True)
#     room_id: UUID = Field(foreign_key="room.id")
#     sender_id: int = Field(foreign_key="user.id")
#     content: str
#     sent_at: datetime
#     is_edited: bool

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlmodel import Field, Relationship, SQLModel

from .base import BaseModel

if TYPE_CHECKING:
    from .room import Room
    from .user import User


class ChatMessageBase(SQLModel):
    content: str
    is_edited: bool = False


class ChatMessagePublic(BaseModel, ChatMessageBase):
    id: int
    room_id: UUID
    sender_id: int


class ChatMessageCreate(ChatMessageBase):
    room_id: UUID
    sender_id: int


class ChatMessageUpdate(ChatMessageBase):
    content: str | None = None
    is_edited: bool | None = None


class ChatMessage(ChatMessagePublic, table=True):
    __tablename__ = 'chat_message'
    id: int | None = Field(default=None, primary_key=True)
    room_id: UUID = Field(foreign_key='room.id')
    sender_id: int = Field(foreign_key='user.id')
    sent_at: datetime | None = None

    room: 'Room' = Relationship(back_populates='messages')
    sender: 'User' = Relationship(back_populates='sent_messages')
