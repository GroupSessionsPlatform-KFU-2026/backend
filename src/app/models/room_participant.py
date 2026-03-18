# from datetime import datetime
# from uuid import UUID, uuid4
# from sqlmodel import SQLModel, Field

# class RoomParticipant(SQLModel, table=True):
#     id: int | None = Field(default=None, primary_key=True)
#     room_id: UUID = Field(foreign_key="room.id")
#     user_id: int = Field(foreign_key="user.id")
#     role: str
#     joined_at: datetime
#     left_at: datetime | None = None
#     is_kicked: bool

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlmodel import Field, Relationship, SQLModel

from .base import BaseModel

if TYPE_CHECKING:
    from .room import Room
    from .user import User


class RoomParticipantBase(SQLModel):
    role: str
    is_kicked: bool = False


class RoomParticipantPublic(BaseModel, RoomParticipantBase):
    id: int
    room_id: UUID
    user_id: int


class RoomParticipantCreate(RoomParticipantBase):
    room_id: UUID
    user_id: int


class RoomParticipantUpdate(RoomParticipantBase):
    role: str | None = None
    is_kicked: bool | None = None


class RoomParticipant(RoomParticipantPublic, table=True):
    __tablename__ = 'room_participant'
    id: int | None = Field(default=None, primary_key=True)
    room_id: UUID = Field(foreign_key='room.id')
    user_id: int = Field(foreign_key='user.id')
    joined_at: datetime | None = None
    left_at: datetime | None = None

    room: 'Room' = Relationship(back_populates='participants')
    user: 'User' = Relationship(back_populates='participations')
