from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlmodel import Relationship, SQLModel

from .base import BaseModel

if TYPE_CHECKING:
    from .room import Room
    from .user import User


class ChatMessageBase(SQLModel):
    content: str


class ChatMessagePublic(BaseModel, ChatMessageBase):
    room_id: UUID
    sender_id: UUID
    sent_at: datetime | None = None
    is_edited: bool


class ChatMessageCreate(ChatMessageBase):
    room_id: UUID
    sender_id: UUID


class ChatMessageUpdate(ChatMessageBase):
    pass


class ChatMessage(ChatMessagePublic, table=True):
    __tablename__ = 'chat_message'

    room: 'Room' = Relationship(back_populates='messages')
    sender: 'User' = Relationship(back_populates='sent_messages')
